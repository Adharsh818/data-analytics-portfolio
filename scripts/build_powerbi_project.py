"""Build a local Power BI project from the exported CSVs and measures.dax.

Run export_powerbi.py first. Open powerbi/olist_dashboard.pbip and refresh in Desktop.
PBIR files follow Microsoft's published JSON schemas; Desktop verification is separate.
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'powerbi'
DATA = ROOT / 'data/processed/powerbi'
SCHEMA = 'https://developer.microsoft.com/json-schemas/fabric/'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def literal(value):
    if isinstance(value, bool):
        value = str(value).lower()
    elif isinstance(value, str):
        value = "'" + value.replace("'", "''") + "'"
    else:
        value = str(value) + 'D'
    return {'expr': {'Literal': {'Value': value}}}


def field(table, column, measure=False):
    return {('Measure' if measure else 'Column'): {
        'Expression': {'SourceRef': {'Entity': table}}, 'Property': column}}


def projection(table, column, measure=False):
    return {'field': field(table, column, measure), 'queryRef': f'{table}.{column}'}


def visual(page, name, kind, title, x, y, width, height, roles=None, sort=None, sync=None):
    config = {'visualType': kind, 'drillFilterOtherVisuals': True,
              'visualContainerObjects': {
                  'title': [{'properties': {'show': literal(True), 'text': literal(title),
                      'fontSize': literal(12), 'fontFamily': literal('Segoe UI'),
                      'fontColor': {'solid': {'color': literal('#1F3A5F')}}}}],
                  'background': [{'properties': {'show': literal(True),
                      'color': {'solid': {'color': literal('#FFFFFF')}}, 'transparency': literal(0)}}]}}
    if roles:
        config['query'] = {'queryState': {r: {'projections': p} for r, p in roles.items()}}
        if sort:
            config['query']['sortDefinition'] = {'sort': [{'field': sort[0], 'direction': sort[1]}],
                                                'isDefaultSort': True}
    if sync:
        config['syncGroup'] = {'groupName': sync, 'fieldChanges': True, 'filterChanges': True}
        config['objects'] = {'data': [{'properties': {'mode': literal('Dropdown')}}]}
    write(OUT / 'Olist.Report/definition/pages' / page / 'visuals' / name / 'visual.json', {
        '$schema': SCHEMA + 'item/report/definition/visualContainer/1.0.0/schema.json',
        'name': name, 'position': {'x': x, 'y': y, 'width': width, 'height': height, 'z': 0, 'tabOrder': y+x},
        'visual': config})


def main():
    if not (DATA / 'fact_orders.csv').exists():
        raise SystemExit('Run python scripts/export_powerbi.py first.')
    tables = []
    integer = {'is_delivered', 'is_late', 'n_items', 'order_item_id', 'installments',
               'recency_days', 'frequency', 'R', 'F', 'M', 'year', 'month_num', 'weekday_num',
               'delivery_bucket_sort'}
    decimal = {'revenue', 'freight', 'review_score', 'delivery_days', 'days_vs_estimate',
               'price', 'freight_value', 'monetary'}
    for name in ['fact_orders', 'fact_order_items', 'dim_customer', 'dim_state', 'dim_date']:
        columns, m_types = [], []
        for col in pd.read_csv(DATA / f'{name}.csv', nrows=0).columns:
            dtype, mtype = ('string', 'type text')
            if col in integer:
                dtype, mtype = 'int64', 'Int64.Type'
            elif col in decimal:
                dtype, mtype = 'double', 'type number'
            elif col in {'date', 'purchase_date'}:
                dtype, mtype = 'dateTime', 'type date'
            definition = {'name': col, 'dataType': dtype, 'sourceColumn': col, 'summarizeBy': 'none'}
            if dtype == 'dateTime':
                definition['formatString'] = 'yyyy-MM-dd'
            if name == 'dim_date' and col == 'date':
                definition['isKey'] = True
                definition['isNullable'] = False
            if name == 'dim_date' and col == 'month':
                definition['sortByColumn'] = 'month_num'
            if name == 'dim_date' and col == 'weekday':
                definition['sortByColumn'] = 'weekday_num'
            if name == 'fact_orders' and col == 'delivery_bucket':
                definition['sortByColumn'] = 'delivery_bucket_sort'
            columns.append(definition)
            m_types.append('{"' + col + '", ' + mtype + '}')
        partition = [
            'let', f'    Source = Csv.Document(File.Contents(DataFolder & "\\{name}.csv"),',
            f'        [Delimiter=",", Columns={len(columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
            '    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
            '    Blanks = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),',
            '    Typed = Table.TransformColumnTypes(Blanks, {' + ', '.join(m_types) + '}, "en-US")',
            'in', '    Typed']
        tables.append({'name': name, 'columns': columns,
            'partitions': [{'name': name, 'mode': 'import', 'source': {'type': 'm', 'expression': partition}}]})
        if name == 'dim_date':
            tables[-1]['dataCategory'] = 'Time'

    dax = re.sub(r'//[^\n]*', '', (OUT / 'measures.dax').read_text(encoding='utf-8'))
    # VAR declarations belong inside the preceding measure; they are not measures.
    matches = list(re.finditer(r'^(?!VAR\b)([A-Za-z][A-Za-z0-9 %]+)[ \t]*=[ \t]*$', dax, re.M | re.I))
    measures = []
    for i, match in enumerate(matches):
        name = match.group(1).strip()
        expr = dax[match.end(): matches[i+1].start() if i+1<len(matches) else len(dax)].strip()
        if not expr:
            raise ValueError(f'Empty DAX expression for measure: {name}')
        fmt = '0.0%' if '%' in name or 'Share' in name else ('#,0.00' if name in {'Avg Review','Avg Order Value'} else '#,0.0' if name == 'Avg Delivery Days' else '#,0')
        if name in {'Total Revenue','Category Revenue','Revenue Prev Month','Avg Order Value'}:
            fmt = '"R$ "' + fmt
        measures.append({'name': name, 'expression': expr.splitlines(), 'formatString': fmt})
    tables[0]['measures'] = measures
    relationships = []
    for name, from_table, from_col, to_table, to_col in [
        ('OrderDate','fact_orders','purchase_date','dim_date','date'),
        ('OrderCustomer','fact_orders','customer_unique_id','dim_customer','customer_unique_id'),
        ('OrderState','fact_orders','customer_state','dim_state','state_code'),
        ('ItemOrder','fact_order_items','order_id','fact_orders','order_id')]:
        relationships.append({'name': name, 'fromTable': from_table, 'fromColumn': from_col,
            'toTable': to_table, 'toColumn': to_col, 'fromCardinality': 'many',
            'toCardinality': 'one', 'crossFilteringBehavior': 'oneDirection', 'isActive': True})
    write(OUT / 'Olist.SemanticModel/model.bim', {'name': 'Olist', 'compatibilityLevel': 1600,
        'model': {'culture': 'en-US', 'defaultPowerBIDataSourceVersion': 'powerBI_V3',
            'sourceQueryCulture': 'en-US', 'tables': tables, 'relationships': relationships,
            'expressions': [{'name': 'DataFolder', 'kind': 'm', 'expression':
                '"' + str(DATA) + '" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}]}})
    write(OUT / 'Olist.SemanticModel/definition.pbism', {'$schema': SCHEMA +
        'item/semanticModel/definitionProperties/1.0.0/schema.json', 'version': '1.0', 'settings': {}})
    write(OUT / 'olist_dashboard.pbip', {'$schema': SCHEMA + 'pbip/pbipProperties/1.0.0/schema.json',
        'version': '1.0', 'artifacts': [{'report': {'path': 'Olist.Report'}}], 'settings': {'enableAutoRecovery': True}})
    write(OUT / 'Olist.Report/definition.pbir', {'$schema': SCHEMA +
        'item/report/definitionProperties/2.0.0/schema.json', 'version': '4.0',
        'datasetReference': {'byPath': {'path': '../Olist.SemanticModel'}}})
    write(OUT / 'Olist.Report/definition/version.json', {'$schema': SCHEMA +
        'item/report/definition/versionMetadata/1.0.0/schema.json', 'version': '1.0.0'})
    write(OUT / 'Olist.Report/definition/report.json', {'$schema': SCHEMA +
        'item/report/definition/report/2.0.0/schema.json', 'themeCollection': {},
        'settings': {'defaultFilterActionIsDataFilter': True}})
    pages = [('Sales', '01 | Sales overview'), ('Delivery', '02 | Delivery and reviews'),
             ('Customers', '03 | Customer purchasing')]
    write(OUT / 'Olist.Report/definition/pages/pages.json', {'$schema': SCHEMA +
        'item/report/definition/pagesMetadata/1.0.0/schema.json', 'pageOrder': [p[0] for p in pages], 'activePageName': 'Sales'})
    for page, title in pages:
        write(OUT / 'Olist.Report/definition/pages' / page / 'page.json', {'$schema': SCHEMA +
            'item/report/definition/page/1.0.0/schema.json', 'name': page, 'displayName': title,
            'displayOption': 'FitToPage', 'height': 720, 'width': 1280})
        for i, (table, col, label) in enumerate([('dim_date','year','Purchase year'),
                ('dim_state','state_code','Customer state'), ('fact_orders','payment_type','Largest payment type')]):
            visual(page, f'{page}Filter{i}', 'slicer', label, 24+i*410, 16, 390, 90,
                   {'Values': [projection(table,col)]}, sync=col)
    metrics = {'Sales': ['Total Revenue','Delivered Orders','Avg Order Value','Customers'],
               'Delivery': ['Late Delivery %','Avg Delivery Days','Avg Review','Bad Review %'],
               'Customers': ['Customers','Repeat Customer %','Total Revenue','Avg Order Value']}
    for page, names in metrics.items():
        for i, name in enumerate(names):
            visual(page, f'{page}KPI{i}', 'card', name, 24+i*310, 120, 294, 115,
                   {'Values': [projection('fact_orders',name,True)]})

    charts = [
        ('Sales','RevenueTrend','lineChart','Monthly delivered merchandise sales (R$)','dim_date','year_month','Total Revenue',24,255,790,210),
        ('Sales','CategorySales','barChart','Category sales (scroll for all categories)','fact_order_items','category','Category Revenue',834,255,420,440),
        ('Sales','StateSales','barChart','Sales by customer state','dim_state','state_code','Total Revenue',24,485,790,210),
        ('Delivery','ReviewLateness','clusteredColumnChart','Review scores by delivery lateness','fact_orders','delivery_bucket','Avg Review',24,255,600,210),
        ('Delivery','StateLateness','barChart','Late rate by state; compare order counts too','dim_state','state_code','Late Delivery %',644,255,610,440),
        ('Delivery','LateTrend','lineChart','Late rate by purchase month','dim_date','year_month','Late Delivery %',24,485,600,210),
        ('Customers','SegmentCustomers','barChart','Customers by full-window RFM segment','dim_customer','segment','Segment Customers',24,255,600,210),
        ('Customers','SegmentSales','barChart','Revenue share by full-window RFM segment','dim_customer','segment','Segment Revenue Share',644,255,610,210),
        ('Customers','CustomerTrend','lineChart','Monthly active purchasing customers','dim_date','year_month','Customers',24,485,1230,210)]
    for page, name, kind, title, table, col, metric, x, y, w, h in charts:
        ascending = col in {'year_month','delivery_bucket'}
        sort = (field(table,col), 'Ascending') if ascending else (field('fact_orders',metric,True),'Descending')
        visual(page,name,kind,title,x,y,w,h,{'Category':[projection(table,col)],
            'Y':[projection('fact_orders',metric,True)]},sort=sort)
    print(f'Built Power BI project: {len(tables)} tables, {len(measures)} measures, 3 pages, 30 visuals.')
    print('Schema validation and a Desktop refresh are separate checks; see BUILD_GUIDE.md.')


if __name__ == '__main__':
    main()
