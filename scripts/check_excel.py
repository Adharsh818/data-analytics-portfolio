"""Audit the saved workbook and prepare a compact visual-verification copy.

Uses openpyxl read-only. Original workbook objects are preserved by patching only
the affected XML cells after Artifact Tool could not import the full workbook.
The compact copy is for preview only: its formula cells use existing saved values.
"""
import json
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np
import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/review-2026-11-05'
SOURCE = ROOT / 'excel/olist_summary.xlsx'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
ET.register_namespace('', NS['s'])


def compact(source, dest):
    with ZipFile(source) as src, ZipFile(dest,'w',ZIP_DEFLATED) as dst:
        for info in src.infolist():
            value = src.read(info.filename)
            if info.filename.startswith('xl/worksheets/sheet') and info.filename.endswith('.xml'):
                sheet = ET.fromstring(value)
                # Cached summary results are sufficient for visual inspection. Never
                # deliver this copy: raw sheets are intentionally reduced to 20 rows.
                for cell in sheet.findall('.//s:c', NS):
                    formula = cell.find('s:f',NS)
                    if formula is not None:
                        sheet_value = cell.find('s:v',NS)
                        cell.remove(formula)
                        if sheet_value is None:
                            cell.attrib.pop('t',None)
                if info.filename in {'xl/worksheets/sheet6.xml','xl/worksheets/sheet7.xml'}:
                    data = sheet.find('s:sheetData',NS)
                    for row in list(data):
                        if int(row.attrib['r'])>21:
                            data.remove(row)
                    sheet.find('s:dimension',NS).set('ref','A1:M21')
                value = ET.tostring(sheet,encoding='utf-8',xml_declaration=True)
            elif info.filename.startswith('xl/tables/') and info.filename.endswith('.xml'):
                table = ET.fromstring(value)
                old = table.attrib.get('ref','')
                if old.endswith('96204'):
                    table.set('ref',old.replace('96204','21'))
                    auto = table.find('s:autoFilter',NS)
                    if auto is not None:
                        auto.set('ref',table.attrib['ref'])
                    value=ET.tostring(table,encoding='utf-8',xml_declaration=True)
            dst.writestr(info,value)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if '--prepare' in sys.argv:
        compact(SOURCE,OUT/'excel-preview-before.xlsx')
        print('Prepared compact cached-value preview; full original remains intact.')
        return
    cached = openpyxl.load_workbook(SOURCE,read_only=True,data_only=True)
    o = pd.DataFrame(cached['Orders'].values)
    o.columns=o.iloc[0]
    o=o.iloc[1:].copy()
    for col in ['revenue','freight','review_score','delivery_days','is_late']:
        o[col]=pd.to_numeric(o[col])
    clean = pd.read_csv(ROOT/'data/processed/orders_clean.csv')
    clean=clean[(clean.order_status=='delivered') & clean.delivery_days.notna()]
    assert set(o.order_id)==set(clean.order_id)
    for col in ['revenue','freight','review_score','is_late']:
        a=o.set_index('order_id')[col].sort_index()
        b=clean.set_index('order_id')[col].sort_index()
        assert np.allclose(a,b,equal_nan=True),col
    assert np.isclose(cached['Dashboard']['C7'].value,o.revenue.sum())
    assert cached['Dashboard']['A7'].value==len(o)
    for row in list(cached['Dashboard'].values)[13:33]:
        month,orders,revenue,aov,_,late,review=row[:7]
        sample=o[o.purchase_month==month]
        assert orders==len(sample)
        assert np.allclose([revenue,aov,late,review],
            [sample.revenue.sum(),sample.revenue.mean(),sample.is_late.mean(),sample.review_score.mean()])
    for row in list(cached['By State'].values)[4:31]:
        state,orders,revenue,share,aov,freight,days,late,review=row[:9]
        sample=o[o.customer_state==state]
        assert orders==len(sample)
        assert np.allclose([revenue,share,aov,freight,days,late,review],
            [sample.revenue.sum(),sample.revenue.sum()/o.revenue.sum(),sample.revenue.mean(),
             sample.freight.sum()/sample.revenue.sum(),sample.delivery_days.mean(),
             sample.is_late.mean(),sample.review_score.mean()])
    revised={}
    for row in range(5,9):
        bucket=cached['Delivery'][f'A{row}'].value
        reviewed=o.loc[o.delivery_bucket==bucket,'review_score'].dropna()
        revised[f'E{row}']=float(reviewed.le(2).mean())
        assert cached['Delivery'][f'F{row}'].value==len(reviewed)
        assert np.isclose(cached['Delivery'][f'D{row}'].value,reviewed.mean())
    cached.close()
    with ZipFile(SOURCE) as src, ZipFile(OUT/'olist_summary.xlsx','w',ZIP_DEFLATED) as dst:
        for info in src.infolist():
            value=src.read(info.filename)
            if info.filename=='xl/worksheets/sheet4.xml':
                tree=ET.fromstring(value)
                title=tree.find('.//s:c[@r="A1"]',NS)
                # Existing file stores the title as an inline string.
                text=title.find('s:is/s:t',NS)
                if text is None:
                    for child in list(title):
                        title.remove(child)
                    title.set('r','A1'); title.set('t','inlineStr'); title.set('s','1')
                    text=ET.SubElement(ET.SubElement(title,'{'+NS['s']+'}is'),'{'+NS['s']+'}t')
                text.text='Review scores by delivery lateness'
                for address,number in revised.items():
                    row=int(address[1:])
                    cell=tree.find(f'.//s:c[@r="{address}"]',NS)
                    cell.find('s:f',NS).text=(f'IF(F{row}=0,"n.a.",COUNTIFS(Orders!$M$2:$M${len(o)+1},A{row},'
                        f'Orders!$I$2:$I${len(o)+1},"<=2",Orders!$I$2:$I${len(o)+1},"<>")/F{row})')
                    cell.find('s:v',NS).text=repr(number)
                value=ET.tostring(tree,encoding='utf-8',xml_declaration=True)
            dst.writestr(info,value)
    with ZipFile(SOURCE) as before,ZipFile(OUT/'olist_summary.xlsx') as after:
        changed=[name for name in before.namelist() if before.read(name)!=after.read(name)]
        assert changed==['xl/worksheets/sheet4.xml'],changed
    # Original parts, tables, charts, formatting and dropdowns remain byte-for-byte
    # identical except this single worksheet. Saved values above are pandas checks,
    # not a claim that a native Excel recalculation was performed.
    # The user's original workbook may be open in Excel. Keep it intact and save
    # the reviewed deliverable under its own name without closing their session.
    reviewed_path=ROOT/'excel/olist_summary_reviewed.xlsx'
    shutil.copy2(OUT/'olist_summary.xlsx',reviewed_path)
    compact(reviewed_path,OUT/'excel-preview-after.xlsx')
    result={'order_rows':len(o),'changed_package_parts':changed,
        'summary_checks':'All 20 monthly and 27 state summaries match workbook order data.',
        'review_share_checks':revised,'reconciliation':'Order IDs, item revenue, freight, review and late flags match pandas.',
        'native_excel_recalculation':'Not performed; original cached values retained, edited cells independently calculated with pandas.'}
    (ROOT/'docs/excel_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
