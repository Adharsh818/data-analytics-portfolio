# Retail Sales & Delivery Analysis | Olist

A personal retail analytics project using **SQL, Python, Excel and Power BI** to answer:
**Where should an online retail team investigate sales performance and customer experience?**

I analysed **96,203 delivered orders**, purchased from January 2017 to August 2018, from
Olist, a Brazilian online marketplace. The work covers data cleaning, sales reporting,
delivery reliability, customer purchasing and seller performance.

This is historical public data, not a project for Target, Lowe's, 7-Eleven or Walmart.
The transferable work is defining retail KPIs, joining transaction tables safely,
checking results and explaining the next business decision.

## Start here

- [Business summary](docs/business_summary.md): findings, priorities and proposed follow-up.
- [Python notebook](notebooks/olist_analysis.ipynb): executed analysis with charts and explanations.
- [Reviewed Excel workbook](excel/olist_summary_reviewed.xlsx): formulas, state selector, trends and category analysis.
- [Power BI project](powerbi/olist_dashboard.pbip): three pages, five tables and 15 DAX measures.
  [Open and refresh instructions](powerbi/BUILD_GUIDE.md).
- [Validation results](docs/validation_results.json) and [review notes](docs/project_review.md).

![Review scores by delivery lateness](notebooks/figures/review_vs_lateness.png)

## Main findings

| Question | What the analysis shows | Business use |
|---|---|---|
| How much was sold? | R$13.18M in delivered merchandise sales; average order value R$137.00. | Establish a consistent sales baseline. |
| Where are delivery problems? | Overall late rate 6.8%; MA 17.5%, CE 13.8%, RJ 12.1%, SP 4.5% among states with 500+ orders. | Prioritise a regional delivery investigation, considering both volume and rate. |
| How do reviews differ? | On-time orders average 4.29 stars; orders 8+ days late average 1.70. | Track promise reliability alongside satisfaction. This is an association, not a causal estimate. |
| Do customers return? | About 3.0% of observed customers have more than one delivered order in the analysis window. | Test a second-purchase campaign, with a control group and equal follow-up time. |
| What changed over time? | November 2017 sales were 52.4% above October; 2018 monthly sales ranged from R$0.83M to R$0.98M. | Review peak-period planning; the data does not isolate promotion effects. |
| How concentrated are sales? | The highest-sales seller decile accounts for about 67% of merchandise sales. | Monitor high-volume sellers and avoid relying on averages alone. |

Supporting queries are in [sales](sql/03_sales.sql), [customers](sql/04_customers.sql),
[delivery](sql/05_delivery.sql), [reviews](sql/06_reviews.sql),
[payments](sql/07_payments.sql) and [sellers](sql/08_sellers.sql).

## What each tool contributes

| Tool | Work demonstrated |
|---|---|
| SQL / SQLite | Joins, CTEs, cleaned views, window functions, monthly growth, cohort retention and customer segmentation. |
| Python / pandas | Source profiling, order-level aggregation, independent reconciliation, RFM scoring and matplotlib charts. |
| Excel | COUNTIFS, SUMIFS, AVERAGEIFS, state dropdown, monthly growth, Pareto analysis and charts. |
| Power BI | Order/item model, single-direction relationships, Power Query CSV imports, DAX measures and three report pages. |

The code uses common analyst tools. RFM and cohorts are explained in the notebook and
[interview guide](docs/interview_guide.md); there is no machine learning model.

## Metric definitions and important limits

- **Revenue** means delivered merchandise sales: sum of item prices, excluding freight.
  It is not profit or Olist's commission revenue. Currency is Brazilian reais (R$).
- Orders must be delivered and have a recorded delivery timestamp. The same population
  is used in SQL, Python, Excel and the Power BI sales measures.
- Orders without items are excluded from the clean model. This means the clean model
  must not be used to calculate an overall cancellation rate.
- Customers use `customer_unique_id`; `customer_id` is an order-specific identifier.
- Multiple source reviews for an order are averaged first. Review averages exclude
  missing scores; bad-review share divides by reviewed orders only.
- Late means delivery on a calendar date after the promised date. Delivery duration
  uses elapsed days. These are different measures.
- Item rows are aggregated before joining to payments or reviews, preventing inflated sales.
  Category and seller review metrics count an order once within each category or seller.
- Retention cohorts begin with the **first observed** delivered purchase in this window.
  Unobserved future months are blank. Low repeat purchase does not establish churn.
- RFM segments use the full window and are descriptive; they are not historical predictions.
- This dataset has no store inventory, stockouts, product costs, margin, staffing or
  promotion exposure. Those metrics cannot be inferred from sales alone.

See the [data dictionary](docs/data_dictionary.md) for table grains and calculation rules.

## Reproduce the analysis

Tested locally with Python 3.12 and pandas 2.2. Download the nine CSVs from the
[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
and extract them directly into `data/raw/`. Do not rename their columns.

From the repository root:

```bash
python -m pip install -r requirements.txt
python scripts/load_data.py
python scripts/run_sql.py
python scripts/build_notebook.py
python scripts/build_excel.py
python scripts/export_powerbi.py
python scripts/build_powerbi_project.py
python scripts/validate_project.py
python scripts/validate_powerbi.py
```

`build_excel.py` is the original Python workbook builder; Excel calculates its formulas
when opened. The existing workbook was preserved separately before review.
`validate_powerbi.py` needs internet on its first run to retrieve Microsoft's schemas.
The Power BI builder sets a local `DataFolder` parameter; regenerate after moving the
repository or change that parameter in Desktop.

**Verification boundary:** the SQL/Python/data-export checks and Power BI JSON schema
checks run locally. Desktop report refresh, DAX execution and visual interactions still
need checking in Power BI Desktop; schema validity alone does not prove them.
See [review notes](docs/project_review.md) for the exact Excel and Desktop status.

## Repository layout

```text
sql/                    schema, cleaned views and business queries
scripts/                load, analyse, export, build and validate
notebooks/              executed notebook and chart images
excel/                  formula-driven summary workbook
powerbi/                PBIP report, semantic model, DAX and opening guide
docs/                   business summary, definitions, validation and interview notes
data/raw/               source CSVs (excluded from Git)
data/processed/          generated database/clean tables (large files excluded)
data/processed/sql_results/  small query outputs included for review
```
