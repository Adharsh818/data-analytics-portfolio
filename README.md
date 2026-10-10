# Olist E-commerce Analytics

End-to-end retail analytics project on ~100k real orders from Olist, a Brazilian online marketplace (2016–2018), built with **SQL, Python, Excel and Power BI**: from raw data to cleaned tables, analysis, and an interactive dashboard with business recommendations.

> ðŸš§ Work in progress. Dataset and business questions are being finalized.

## Tools
| Tool | Used for |
|------|----------|
| SQL | Data modeling, cleaning, and business queries |
| Python (pandas, matplotlib/seaborn) | EDA, cleaning, cohort/RFM analysis |
| Excel | Pivot tables, quick summaries, what-if analysis |
| Power BI | Interactive dashboard and KPIs |

## Repository structure
```
data/
  raw/         # original downloaded data (not committed, see "Data" below)
  processed/   # cleaned outputs used by SQL / Power BI
sql/           # schema, cleaning, and analysis queries
notebooks/     # Jupyter notebooks for EDA and analysis
excel/         # Excel workbooks (pivots, summaries)
powerbi/       # .pbix dashboard and screenshots
scripts/       # Python scripts (data loading)
```

## Data
[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) on Kaggle: 9 related tables covering orders, items, payments, reviews, customers, sellers, products and geolocation.

The raw CSVs are not committed. To get them, download the zip from Kaggle and extract the 9 CSV files into `data/raw/`.

## Business questions
Framed the way a retail analytics team would ask them:

1. **Sales performance:** How have revenue and order volume trended month over month? Which categories and states drive the most revenue?
2. **Customers:** What share of customers buy again? How do monthly cohorts retain? Who are the high-value customers (RFM segments)?
3. **Delivery:** How often are orders late versus the promised date, and where is it worst?
4. **Satisfaction:** How does late delivery affect review scores? Which categories get the worst reviews?
5. **Payments:** How do payment type and installments relate to order value?
6. **Sellers:** Which sellers drive revenue, and which hurt customer experience?

## Key insights
_To be added._

## How to reproduce
```bash
pip install pandas
python scripts/load_data.py   # builds data/processed/olist.db from data/raw/*.csv
```
SQL queries in `sql/` run against `olist.db` (SQLite; open it with DB Browser for SQLite or DBeaver).
