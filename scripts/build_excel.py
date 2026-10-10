"""Build excel/olist_summary.xlsx from the cleaned tables.

Sheets:
  About         what the workbook is and how it was built
  Dashboard     KPI cards with a state selector, monthly trend with MoM growth, chart
  By State      revenue, delivery and review metrics per state (SUMIFS / AVERAGEIFS)
  Delivery      review score by delivery lateness, with chart
  Categories    category revenue Pareto (share and cumulative share)
  Orders        order-level data table (delivered orders, Jan 2017 - Aug 2018)
  Category Data category totals pre-aggregated in Python from order items

Every summary number is an Excel formula over the Orders / Category Data sheets.

Usage: python scripts/build_excel.py   (run scripts/build_notebook.py first)
"""
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
OUT = ROOT / "excel" / "olist_summary.xlsx"

FONT = "Arial"
NAVY = "1F3A5F"
H_FILL = PatternFill("solid", fgColor=NAVY)
CARD_FILL = PatternFill("solid", fgColor="EEF3FA")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
THIN = Side(style="thin", color="C9D3E0")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

BUCKETS = ["On time / early", "1-3 days late", "4-7 days late", "8+ days late"]


def f(bold=False, size=10, color="000000", italic=False):
    return Font(name=FONT, bold=bold, size=size, color=color, italic=italic)


def header_row(ws, row, headers, col=1):
    for i, h in enumerate(headers):
        c = ws.cell(row=row, column=col + i, value=h)
        c.font = f(bold=True, color="FFFFFF")
        c.fill = H_FILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BOX


def title(ws, text, sub=None):
    ws["A1"] = text
    ws["A1"].font = f(bold=True, size=16, color=NAVY)
    if sub:
        ws["A2"] = sub
        ws["A2"].font = f(italic=True, color="555555")
    ws.sheet_view.showGridLines = False


def widths(ws, mapping):
    for col, w in mapping.items():
        ws.column_dimensions[col].width = w


def load():
    o = pd.read_csv(PROC / "orders_clean.csv")
    o = o[(o["order_status"] == "delivered") & o["delivery_days"].notna()].copy()
    o["delivery_bucket"] = pd.cut(o["days_vs_estimate"], [-1e9, 0, 3, 7, 1e9], labels=BUCKETS).astype(str)
    o = o[["order_id", "purchase_month", "customer_state", "payment_type", "installments", "n_items",
           "revenue", "freight", "review_score", "delivery_days", "days_vs_estimate", "is_late", "delivery_bucket"]]
    o["delivery_days"] = o["delivery_days"].round(1)
    o["payment_type"] = o["payment_type"].fillna("unknown")

    items = pd.read_csv(PROC / "order_items_clean.csv")
    items = items[items["order_id"].isin(o["order_id"])]
    cat = (items.groupby("category").agg(orders=("order_id", "nunique"), items=("order_item_id", "count"),
                                         revenue=("price", "sum"))
           .sort_values("revenue", ascending=False).reset_index())
    cat["revenue"] = cat["revenue"].round(2)
    return o, cat


def write_table(ws, df, name, start_row=1):
    for j, col in enumerate(df.columns, 1):
        ws.cell(row=start_row, column=j, value=col)
    for r in df.itertuples(index=False):
        ws.append([None if (isinstance(v, float) and pd.isna(v)) else v for v in r])
    last = start_row + len(df)
    ref = f"A{start_row}:{get_column_letter(df.shape[1])}{last}"
    t = Table(displayName=name, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(t)
    ws.freeze_panes = ws.cell(row=start_row + 1, column=1)
    for j, col in enumerate(df.columns, 1):
        ws.column_dimensions[get_column_letter(j)].width = max(12, len(col) + 3)
    return last


def main() -> None:
    o, cat = load()
    n = len(o) + 1  # last data row on Orders
    months = sorted(o["purchase_month"].unique())
    states = o.groupby("customer_state")["revenue"].sum().sort_values(ascending=False).index.tolist()

    wb = Workbook()

    # ---------- Orders (data) ----------
    ws_o = wb.active
    ws_o.title = "Orders"
    write_table(ws_o, o, "Orders")
    for col, fmt in {"G": "#,##0.00", "H": "#,##0.00", "I": "0.0", "J": "0.0"}.items():
        for c in ws_o[f"{col}2:{col}{n}"]:
            c[0].number_format = fmt
    ws_o.column_dimensions["A"].width = 36

    # Named column ranges keep the summary formulas readable
    R = {name: f"Orders!${col}$2:${col}${n}" for name, col in {
        "month": "B", "state": "C", "pay": "D", "rev": "G", "freight": "H", "review": "I",
        "days": "J", "late": "L", "bucket": "M"}.items()}

    # ---------- Category Data ----------
    ws_cd = wb.create_sheet("Category Data")
    n_cat = write_table(ws_cd, cat, "CategoryData")
    ws_cd.column_dimensions["A"].width = 40
    for c in ws_cd[f"D2:D{n_cat}"]:
        c[0].number_format = "#,##0"

    # ---------- Dashboard ----------
    ws = wb.create_sheet("Dashboard", 0)
    title(ws, "Olist E-commerce: Sales Dashboard",
          "Delivered orders, Jan 2017 - Aug 2018. Revenue = item price in Brazilian reais (R$), excluding freight.")
    ws["A4"] = "State filter:"
    ws["A4"].font = f(bold=True)
    ws["B4"] = "All"
    ws["B4"].fill = INPUT_FILL
    ws["B4"].font = f(bold=True, color="0000FF")
    ws["B4"].border = BOX
    ws["C4"] = "<- pick a state (yellow cell) to filter the KPI cards"
    ws["C4"].font = f(italic=True, color="555555")
    # dropdown list lives in hidden column Z
    ws["Z1"] = "All"
    for i, s in enumerate(states, 2):
        ws[f"Z{i}"] = s
    ws.column_dimensions["Z"].hidden = True
    dv = DataValidation(type="list", formula1=f"=$Z$1:$Z${len(states) + 1}", allow_blank=False)
    ws.add_data_validation(dv)
    dv.add("B4")

    crit = 'IF($B$4="All","*",$B$4)'
    cards = [
        ("Orders", f'=COUNTIFS({R["state"]},{crit})', "#,##0"),
        ("Revenue (R$)", f'=SUMIFS({R["rev"]},{R["state"]},{crit})', "#,##0"),
        ("Avg order value (R$)", "=IFERROR(C7/A7,0)", "#,##0.00"),
        ("Avg review (1-5)", f'=IFERROR(AVERAGEIFS({R["review"]},{R["state"]},{crit}),0)', "0.00"),
        ("Avg delivery days", f'=IFERROR(AVERAGEIFS({R["days"]},{R["state"]},{crit}),0)', "0.0"),
        ("Late deliveries", f'=IFERROR(SUMIFS({R["late"]},{R["state"]},{crit})/A7,0)', "0.0%"),
    ]
    for i, (label, formula, fmt) in enumerate(cards):
        col = 1 + i * 2 if i < 3 else 1 + (i - 3) * 2
        row = 6 if i < 3 else 9
        lc = ws.cell(row=row, column=col, value=label)
        vc = ws.cell(row=row + 1, column=col, value=formula)
        lc.font = f(bold=True, color="555555", size=9)
        vc.font = f(bold=True, size=16, color=NAVY)
        vc.number_format = fmt
        for c in (lc, vc):
            c.fill = CARD_FILL
            c.border = BOX
            c.alignment = Alignment(horizontal="center")
        ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col + 1)
        ws.merge_cells(start_row=row + 1, start_column=col, end_row=row + 1, end_column=col + 1)
    # card formulas reference A7 (orders) and C7 (revenue) - fixed positions above

    ws["A12"] = "Monthly trend (all states)"
    ws["A12"].font = f(bold=True, size=12, color=NAVY)
    header_row(ws, 13, ["Month", "Orders", "Revenue (R$)", "Avg order value (R$)", "MoM revenue growth",
                        "Late deliveries", "Avg review"])
    for i, m in enumerate(months):
        r = 14 + i
        ws.cell(row=r, column=1, value=m)
        ws.cell(row=r, column=2, value=f'=COUNTIFS({R["month"]},A{r})').number_format = "#,##0"
        ws.cell(row=r, column=3, value=f'=SUMIFS({R["rev"]},{R["month"]},A{r})').number_format = "#,##0"
        ws.cell(row=r, column=4, value=f"=IFERROR(C{r}/B{r},0)").number_format = "#,##0.00"
        ws.cell(row=r, column=5, value=None if i == 0 else f"=IFERROR(C{r}/C{r - 1}-1,0)").number_format = "0.0%;[Red]-0.0%"
        ws.cell(row=r, column=6, value=f'=IFERROR(SUMIFS({R["late"]},{R["month"]},A{r})/B{r},0)').number_format = "0.0%"
        ws.cell(row=r, column=7, value=f'=IFERROR(AVERAGEIFS({R["review"]},{R["month"]},A{r}),0)').number_format = "0.00"
        for c in range(1, 8):
            ws.cell(row=r, column=c).font = f()
            ws.cell(row=r, column=c).border = BOX
    last_m = 13 + len(months)
    tr = last_m + 1
    ws.cell(row=tr, column=1, value="Total")
    ws.cell(row=tr, column=2, value=f"=SUM(B14:B{last_m})").number_format = "#,##0"
    ws.cell(row=tr, column=3, value=f"=SUM(C14:C{last_m})").number_format = "#,##0"
    ws.cell(row=tr, column=4, value=f"=IFERROR(C{tr}/B{tr},0)").number_format = "#,##0.00"
    for c in range(1, 8):
        ws.cell(row=tr, column=c).font = f(bold=True)
        ws.cell(row=tr, column=c).border = BOX
    ws.conditional_formatting.add(f"F14:F{last_m}", ColorScaleRule(start_type="min", start_color="FFFFFF",
                                                                   end_type="max", end_color="F4A6A6"))

    chart = BarChart()
    chart.title = "Monthly revenue (R$)"
    chart.y_axis.title = "Revenue"
    chart.add_data(Reference(ws, min_col=3, min_row=13, max_row=last_m), titles_from_data=True)
    chart.set_categories(Reference(ws, min_col=1, min_row=14, max_row=last_m))
    chart.legend = None
    chart.height, chart.width = 8, 18
    line = LineChart()
    line.add_data(Reference(ws, min_col=6, min_row=13, max_row=last_m), titles_from_data=True)
    line.y_axis.axId = 200
    line.y_axis.title = "Late deliveries"
    line.y_axis.number_format = "0%"
    line.y_axis.crosses = "max"
    chart += line
    ws.add_chart(chart, "I12")
    widths(ws, {"A": 16, "B": 12, "C": 15, "D": 14, "E": 14, "F": 14, "G": 12})

    # ---------- By State ----------
    ws_s = wb.create_sheet("By State", 1)
    title(ws_s, "Performance by customer state", "Sorted by revenue. Late % and review use the same delivered orders.")
    header_row(ws_s, 4, ["State", "Orders", "Revenue (R$)", "Revenue share", "Avg order value (R$)",
                         "Freight as % of revenue", "Avg delivery days", "Late deliveries", "Avg review"])
    for i, s in enumerate(states):
        r = 5 + i
        ws_s.cell(row=r, column=1, value=s)
        ws_s.cell(row=r, column=2, value=f'=COUNTIFS({R["state"]},A{r})').number_format = "#,##0"
        ws_s.cell(row=r, column=3, value=f'=SUMIFS({R["rev"]},{R["state"]},A{r})').number_format = "#,##0"
        ws_s.cell(row=r, column=4, value=f"=C{r}/SUM($C$5:$C${4 + len(states)})").number_format = "0.0%"
        ws_s.cell(row=r, column=5, value=f"=IFERROR(C{r}/B{r},0)").number_format = "#,##0.00"
        ws_s.cell(row=r, column=6, value=f'=IFERROR(SUMIFS({R["freight"]},{R["state"]},A{r})/C{r},0)').number_format = "0.0%"
        ws_s.cell(row=r, column=7, value=f'=IFERROR(AVERAGEIFS({R["days"]},{R["state"]},A{r}),0)').number_format = "0.0"
        ws_s.cell(row=r, column=8, value=f'=IFERROR(SUMIFS({R["late"]},{R["state"]},A{r})/B{r},0)').number_format = "0.0%"
        ws_s.cell(row=r, column=9, value=f'=IFERROR(AVERAGEIFS({R["review"]},{R["state"]},A{r}),0)').number_format = "0.00"
        for c in range(1, 10):
            ws_s.cell(row=r, column=c).font = f()
            ws_s.cell(row=r, column=c).border = BOX
    end = 4 + len(states)
    ws_s.conditional_formatting.add(f"C5:C{end}", DataBarRule(start_type="min", end_type="max", color="5B8DEF"))
    ws_s.conditional_formatting.add(f"H5:H{end}", ColorScaleRule(start_type="min", start_color="FFFFFF",
                                                                 end_type="max", end_color="F4A6A6"))
    ws_s.conditional_formatting.add(f"I5:I{end}", ColorScaleRule(start_type="min", start_color="F4A6A6",
                                                                 end_type="max", end_color="FFFFFF"))
    ws_s.freeze_panes = "B5"
    widths(ws_s, {"A": 10, "B": 10, "C": 15, "D": 12, "E": 14, "F": 14, "G": 12, "H": 12, "I": 11})

    # ---------- Delivery ----------
    ws_d = wb.create_sheet("Delivery", 2)
    title(ws_d, "Does late delivery hurt reviews?",
          "Delivery lateness = delivered date minus the estimated date shown to the customer at purchase.")
    header_row(ws_d, 4, ["Delivery vs promise", "Orders", "Share of orders", "Avg review", "1-2 star reviews",
                         "Reviews counted"])
    for i, b in enumerate(BUCKETS):
        r = 5 + i
        ws_d.cell(row=r, column=1, value=b)
        ws_d.cell(row=r, column=2, value=f'=COUNTIFS({R["bucket"]},A{r})').number_format = "#,##0"
        ws_d.cell(row=r, column=3, value=f"=B{r}/SUM($B$5:$B$8)").number_format = "0.0%"
        ws_d.cell(row=r, column=4, value=f'=AVERAGEIFS({R["review"]},{R["bucket"]},A{r})').number_format = "0.00"
        ws_d.cell(row=r, column=6, value=f'=COUNTIFS({R["bucket"]},A{r},{R["review"]},"<>")').number_format = "#,##0"
        ws_d.cell(row=r, column=5, value=f'=COUNTIFS({R["bucket"]},A{r},{R["review"]},"<=2")/F{r}').number_format = "0.0%"
        for c in range(1, 7):
            ws_d.cell(row=r, column=c).font = f()
            ws_d.cell(row=r, column=c).border = BOX
    ws_d["A10"] = "Takeaway"
    ws_d["A10"].font = f(bold=True, color=NAVY)
    ws_d["A11"] = '="Orders 8+ days late average "&TEXT(D8,"0.00")&" stars vs "&TEXT(D5,"0.00")&" for on-time orders."'
    ws_d["A11"].font = f()
    ch = BarChart()
    ch.title = "Average review by delivery lateness"
    ch.add_data(Reference(ws_d, min_col=4, min_row=4, max_row=8), titles_from_data=True)
    ch.set_categories(Reference(ws_d, min_col=1, min_row=5, max_row=8))
    ch.y_axis.scaling.min, ch.y_axis.scaling.max = 0, 5
    ch.legend = None
    ch.height, ch.width = 8, 14
    ws_d.add_chart(ch, "A13")
    widths(ws_d, {"A": 22, "B": 10, "C": 14, "D": 11, "E": 14, "F": 14})

    # ---------- Categories ----------
    ws_c = wb.create_sheet("Categories", 3)
    title(ws_c, "Category revenue (Pareto)", "Source: Category Data sheet (order items of delivered orders).")
    header_row(ws_c, 4, ["Rank", "Category", "Orders", "Revenue (R$)", "Revenue share", "Cumulative share"])
    for i in range(n_cat - 1):
        r, src = 5 + i, 2 + i
        ws_c.cell(row=r, column=1, value=i + 1)
        ws_c.cell(row=r, column=2, value=f"='Category Data'!A{src}")
        ws_c.cell(row=r, column=3, value=f"='Category Data'!B{src}").number_format = "#,##0"
        ws_c.cell(row=r, column=4, value=f"='Category Data'!D{src}").number_format = "#,##0"
        ws_c.cell(row=r, column=5, value=f"=D{r}/SUM($D$5:$D${3 + n_cat})").number_format = "0.0%"
        ws_c.cell(row=r, column=6, value=f"=SUM($D$5:D{r})/SUM($D$5:$D${3 + n_cat})").number_format = "0.0%"
        for c in range(1, 7):
            ws_c.cell(row=r, column=c).font = f(color="008000") if c in (2, 3, 4) else f()
            ws_c.cell(row=r, column=c).border = BOX
    ws_c.conditional_formatting.add(f"D5:D{3 + n_cat}", DataBarRule(start_type="min", end_type="max", color="5B8DEF"))
    ws_c["H4"] = "Categories needed for 80% of revenue:"
    ws_c["H4"].font = f(bold=True)
    ws_c["H5"] = f'=COUNTIF(F5:F{3 + n_cat},"<0.8")+1'
    ws_c["H5"].font = f(bold=True, size=14, color=NAVY)
    ws_c.freeze_panes = "C5"
    widths(ws_c, {"A": 7, "B": 38, "C": 10, "D": 15, "E": 13, "F": 15, "H": 36})

    # ---------- About ----------
    ws_a = wb.create_sheet("About", 0)
    title(ws_a, "Olist E-commerce Summary Workbook")
    rows = [
        ("Purpose", "Excel companion to the SQL / Python / Power BI analysis of ~96k delivered Olist orders."),
        ("Data source", "Brazilian E-Commerce Public Dataset by Olist (Kaggle): kaggle.com/datasets/olistbr/brazilian-ecommerce"),
        ("Scope", "Delivered orders purchased Jan 2017 - Aug 2018 (full months only)."),
        ("Revenue", "Sum of item prices in Brazilian reais (R$), excluding freight."),
        ("Late delivery", "Delivered after the estimated delivery date shown to the customer."),
        ("How it's built", "Orders and Category Data are exported by notebooks/olist_analysis.py; every other "
                           "sheet is Excel formulas (COUNTIFS, SUMIFS, AVERAGEIFS) over those sheets."),
        ("Sheets", "Dashboard (KPIs + state filter + monthly trend), By State, Delivery, Categories, Orders, Category Data."),
        ("Try it", "Change the yellow State filter on Dashboard. Or insert a PivotTable from the Orders table "
                   "(Insert > PivotTable) with customer_state in Rows and revenue in Values."),
    ]
    for i, (k, v) in enumerate(rows, 3):
        ws_a.cell(row=i, column=1, value=k).font = f(bold=True)
        c = ws_a.cell(row=i, column=2, value=v)
        c.font = f()
        c.alignment = Alignment(wrap_text=True, vertical="top")
        ws_a.row_dimensions[i].height = 30
    widths(ws_a, {"A": 16, "B": 100})

    wb.active = wb.sheetnames.index("Dashboard")
    wb.calculation.fullCalcOnLoad = True
    OUT.parent.mkdir(exist_ok=True)
    wb.save(OUT)
    print(f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e6:.1f} MB), {len(o):,} order rows, {len(cat)} categories")


if __name__ == "__main__":
    main()
