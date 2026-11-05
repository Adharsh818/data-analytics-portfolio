"""Package the Power BI project and prepared data for a GitHub release.

Run the analysis/export pipeline first. No raw CSVs or local data caches are packaged.
The Excel workbook is a separate release download.
"""
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/releases/olist_powerbi_dashboard.zip'


def main():
    project = ROOT / 'powerbi'
    files = [project / 'olist_dashboard.pbip', project / 'measures.dax', project / 'BUILD_GUIDE.md',
             ROOT / 'docs/data_dictionary.md', ROOT / 'docs/validation.md',
             ROOT / 'docs/validation_results.json']
    files += sorted((project / 'Olist.Report').rglob('*.json'))
    files += [project / 'Olist.Report/definition.pbir',
              project / 'Olist.Report/.platform',
              project / 'Olist.SemanticModel/definition.pbism',
              project / 'Olist.SemanticModel/.platform',
              project / 'Olist.SemanticModel/model.bim']
    for name in ['fact_orders', 'fact_order_items', 'dim_customer', 'dim_state', 'dim_date']:
        files.append(ROOT / f'data/processed/powerbi/{name}.csv')
    missing = [str(p.relative_to(ROOT)) for p in files if not p.exists()]
    if missing:
        raise SystemExit('Missing files; rebuild/export the project first: ' + ', '.join(missing))
    instructions = '''# Olist Power BI dashboard

1. Extract this entire ZIP to a local folder.
2. Open powerbi/olist_dashboard.pbip in current Power BI Desktop with PBIP/PBIR support.
3. Go to Transform data > Manage parameters. Set DataFolder to the FULL path of
   the extracted data/processed/powerbi folder, then apply and refresh.
4. Use powerbi/BUILD_GUIDE.md to check the baseline and test the filters.

Pages: Sales Overview, Delivery & Reviews, Customer Purchasing.
Baseline: 96,203 delivered orders; 93,096 customers; R$13,179,777.95 merchandise sales.
The project contains no imported data cache; the five prepared CSVs are included.

SQL/pandas/export checks and report JSON schema checks passed. Native Desktop
refresh, DAX execution and report interactions still require verification.
This is a local Power BI project, not a hosted report or a verified PBIX.

Source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
Project: https://github.com/Adharsh818/data-analytics-portfolio
'''
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUT, 'w', ZIP_DEFLATED) as bundle:
        bundle.writestr('START_HERE.md', instructions)
        for file in files:
            relative = file.relative_to(ROOT).as_posix()
            if file.name == 'model.bim':
                model = json.loads(file.read_text(encoding='utf-8'))
                for expression in model['model']['expressions']:
                    if expression['name'] == 'DataFolder':
                        expression['expression'] = ('"C:\\Olist\\data\\processed\\powerbi" '
                            'meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]')
                bundle.writestr(relative, json.dumps(model, indent=2) + '\n')
            else:
                bundle.write(file, relative)
    with ZipFile(OUT) as bundle:
        assert bundle.testzip() is None
        assert len([p for p in bundle.namelist() if p.endswith('.csv')]) == 5
        assert not any('/raw/' in p or '/.pbi/' in p for p in bundle.namelist())
    print(f'Created {OUT.relative_to(ROOT)}: {OUT.stat().st_size / 1e6:.1f} MB; {len(files)} project/data files.')


if __name__ == '__main__':
    main()
