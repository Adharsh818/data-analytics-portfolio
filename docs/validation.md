# Validation and dashboard status

The analysis uses 96,203 delivered orders, 93,096 customers and R$13,179,777.95 in
merchandise sales. Sales exclude freight. Validation was run on 5 November 2026.

## Completed checks

- Rebuilt SQLite from the nine source CSVs, reran all 18 SQL queries and executed the notebook.
- Passed 28 data checks covering raw keys, relationships, analysis eligibility,
  SQL/pandas order-level values, sales totals, customer segments, cohort observation
  windows, category/seller review averages and Power BI export relationships.
- Validated 39 PBIP/PBIR files against Microsoft's public JSON schemas and checked
  that report field references and the four relationships point to model fields.
- Compared the Excel source-order data against pandas, including IDs, revenue,
  freight, review scores and late flags. Checked all 20 monthly and 27 state summaries.
- Preserved the workbook's charts, tables and state dropdown. The revised review-share
  formula explicitly excludes missing scores and passed a small spreadsheet-engine
  test that included a missing score and a changed input.

The data-check results are available in [validation_results.json](validation_results.json).
Run `python scripts/validate_project.py` and `python scripts/validate_powerbi.py` to
repeat the data and report-structure checks after rebuilding.

## Native application checks still required

The available desktop automation could not initialize during the review. Consequently,
the saved Excel results were independently checked without a native Excel recalculation,
and the Power BI project has not been refreshed or visually verified in Desktop.

Before treating either dashboard as fully tested:

1. Open the Excel workbook, recalculate, change the state selector and confirm the KPI
   cards update. The monthly trend and supporting sheets intentionally show all states.
2. Extract the Power BI download, set its `DataFolder` parameter, refresh, check baseline
   values and test the state/year/payment slicers. Save and reopen the report.

Use the expected values and filter cases in the [Power BI opening guide](../powerbi/BUILD_GUIDE.md).
JSON schema validity checks file structure; it does not prove DAX execution, Power Query
refresh, visual layout or interactions. The download is an editable PBIP project,
not a published Power BI Service report or a Desktop-verified PBIX.
