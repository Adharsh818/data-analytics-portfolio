# Project review — 5 November 2026

## Assessment

This is a suitable early-career retail analytics project: real linked transaction
data, explicit business questions, SQL, pandas, Excel formulas and a Power BI model.
Its strongest interview story is how correct transaction grain and consistent
definitions support sales and fulfilment decisions. The analysis remains descriptive
and readable; there is no need to add machine learning to make it more credible.

The data represents a Brazilian online marketplace, not store operations in Bengaluru.
Present the methods as transferable and explain which data a retailer would need next.

## Completed repairs

| Area | Problem found | Change |
|---|---|---|
| SQL reviews | Multi-item orders received extra weight in category and seller averages. | Deduplicate category/order and seller/order pairs before averaging; preserve item-price revenue separately. |
| Cohorts | SQL reported zero for follow-up months that had not happened. | Future months now return NULL; Python shows observed zeroes and masks future cells. |
| Customer segments | SQL NTILE could split tied values, differing from Python qcut. | Both now use cumulative percentile ranks with ties kept together. |
| Freight ratio | SQL averaged order ratios while Excel calculated a ratio of totals. | Use total freight / total item revenue consistently. |
| Unknown promises | SQL could mark an unknown estimated date as on time. | Leave lateness unknown if either required delivery date is missing. |
| Power BI population | Delivered flags included orders missing a delivery timestamp. | Align eligibility with SQL, Python and Excel. |
| Power BI reviews | DAX comparison could include blank scores as bad reviews. | Explicitly exclude missing scores from the numerator and denominator. |
| Power BI customers | Dimension-row counts ignored date/state/payment context. | Count delivered customers from the filtered fact table. |
| Cancellation metric | Clean data excluded itemless orders, making cancellation rates incomplete. | Remove this measure; document the excluded population. |
| Power BI deliverable | Only DAX and a manual build guide existed. | Add a PBIP project with five tables, relationships, CSV imports, 15 measures and 30 visuals across three pages. |
| Excel | Review-share formula lacked an explicit missing-score guard; title implied causality. | Add explicit review eligibility and use an observational title; preserve the rest of the workbook. |
| Claims | Delivery and installment associations were described as causes. | Rewrite findings and recommendations as observations and proposed tests. |
| Reproduction | Dependency list and reconciliation script were missing. | Add requirements, validation scripts and clearer refresh instructions. |

Raw data was available locally. The database was rebuilt from all nine raw CSVs, all
18 named SQL queries were rerun, the notebook was executed again, and clean data and
Power BI exports were regenerated. Small SQL outputs and chart images were refreshed.

## Verification performed

- **28 data checks passed**: raw keys, source relationships, order-level SQL/pandas
  values, revenue, eligibility, RFM segment counts, all 80 cohort retention cells,
  category/seller review averages and Power BI export relationships.
- Baseline: **96,203 orders; 93,096 customers; R$13,179,777.95 merchandise sales**.
- **39 PBIP/PBIR JSON definitions** pass Microsoft's public schemas. This validates
  structure; it does not execute DAX/M or prove that visual role mappings work in Desktop.
- The saved Excel order data matches pandas, including order IDs, revenue, freight,
  review scores and late flags. Monthly and state summaries were independently compared.
- Only the Delivery worksheet XML changes in the repaired workbook. Other package parts,
  including charts, tables, dropdowns, source sheets and formatting, are unchanged.
- A compact copy of cached workbook results was rendered for visual review. The full
  workbook could not be imported by Artifact Tool because it exceeded the 4 GB heap limit.
  Its renderer also omits some overflow text and chart-axis details, so these previews
  are not evidence of native Excel display fidelity.
- A representative spreadsheet formula test confirms that missing review scores are
  excluded and that the result responds to changed scores. It is not a full native
  Excel recalculation or state-dropdown interaction test.
- Python files compile and the Git whitespace check passes.

Details: [data validation](validation_results.json), [Excel validation](excel_validation.json).

## Files preserved and saved

The original `excel/olist_summary.xlsx` already had local changes when this review
started. It was open/locked and was left intact. The final reviewed workbook is
`excel/olist_summary_reviewed.xlsx`, mirrored in `outputs/review-2026-11-05/`.
A pre-review backup and temporary verification previews are in that ignored output folder.
No Git commit, push, public upload or online publishing was performed.

## Checks still requiring Desktop

Both available Desktop automation interfaces failed during initialization with
`failed to write kernel assets: The system cannot find the path specified`.
Consequently, the following work is **not verified**:

1. Open/refresh/save/reopen the Power BI project, check the data model and DAX card
   values, and test state/year/payment filtering. Use the exact cases in
   [Power BI instructions](../powerbi/BUILD_GUIDE.md). Save authentic screenshots afterward.
2. Open the reviewed workbook in Excel, recalculate and test the state dropdown.
   It filters the KPI cards only; the monthly trend and supporting sheets show all states.

The Power BI report is delivered as editable project files, not as a Desktop-verified
PBIX. Do not describe it as published or fully tested until the checks above pass.
The Excel file retains saved results checked against pandas; no native recalculation
was performed during this review.

## Before interviews

Read the [interview guide](interview_guide.md), practise the join/denominator explanations
and run the project once yourself. Use the resume bullets that you can demonstrate.
