# Validation and dashboard status

The analysis uses 96,203 delivered orders, 93,096 customers and R$13,179,777.95 in
merchandise sales. Sales exclude freight. Data and structural validation were rerun on 6 November 2026.

## Completed checks

- Rebuilt SQLite from the nine source CSVs, reran all 18 SQL queries and executed the notebook.
- Passed 28 data checks covering raw keys, relationships, analysis eligibility,
  SQL/pandas order-level values, sales totals, customer segments, cohort observation
  windows, category/seller review averages and Power BI export relationships.
- Validated 39 PBIP/PBIR files against Microsoft's public JSON schemas and checked
  that report field references and the four relationships point to model fields.
- On 6 November, corrected a DAX-header parsing error that treated `VAR cust` as a
  separate measure. The generator now retains the complete Repeat Customer % body;
  regression checks verify 14 nonempty business measures and its VAR/RETURN expression.
- A subsequent compatibility review corrected the enhanced report content version to
  `2.0.0`, included report/model platform metadata, and added page/visual presence and
  report-format checks. A clean rebuild passes 41 schema checks; Desktop-saved files
  may omit some schema declarations and produce a different count. The saved native
  project passes 38 schema checks, with 14 business measures and five relationships
  including one Desktop-generated auto-date relationship.
- Compared the Excel source-order data against pandas, including IDs, revenue,
  freight, review scores and late flags. Checked all 20 monthly and 27 state summaries.
- Preserved the workbook's charts, tables and state dropdown. The revised review-share
  formula explicitly excludes missing scores and passed a small spreadsheet-engine
  test that included a missing score and a changed input. A subsequent XML repair
  preserves the original worksheet namespace declarations and all ZIP parts except
  the intentionally corrected Delivery sheet. Reopening the corrected file in Excel
  remains a separate application check.

The data-check results are available in [validation_results.json](validation_results.json).
Run `python scripts/validate_project.py` and `python scripts/validate_powerbi.py` to
repeat the data and report-structure checks after rebuilding.

## Native application evidence and remaining checks

On 6 November 2026, the project owner confirmed that all three recovered Power BI
pages open and that the charts and baseline totals match. The supplied Desktop
screenshots are included in the README. Visible values include AOV R$137.00, late
rate 6.8%, average review 4.16, delivery duration 12.5 days and repeat share 3.0%.
Revenue, order and customer cards use rounded display units in the images; the owner
also confirmed the expected underlying totals in the conversation.

This confirms baseline rendering and the visible measures in that session. It does
not independently establish a fresh import on another computer, every unused measure,
combined filter behaviour or every refresh/save/reopen scenario. Desktop automation
remained unavailable to the reviewing assistant.

Remaining checks before treating the dashboards as fully tested:

1. Open the Excel workbook, recalculate, change the state selector and confirm the KPI
   cards update. The monthly trend and supporting sheets intentionally show all states.
2. Extract the Power BI download, set its `DataFolder` parameter, refresh, check baseline
   values and test the state/year/payment slicers. Save and reopen the report.

Use the expected values and filter cases in the [Power BI opening guide](../powerbi/BUILD_GUIDE.md).
JSON schema validity checks file structure; it does not prove DAX execution, Power Query
refresh, visual layout or interactions by itself. The download is an editable PBIP
project, not a published Power BI Service report or a saved PBIX deliverable.
