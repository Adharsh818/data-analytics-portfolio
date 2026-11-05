"""Reconcile independent SQL, pandas and Power BI exports, failing on mismatches.

Run after run_sql.py, build_notebook.py and export_powerbi.py.
Writes a small, readable validation report for reviewers.
"""
import json
import sqlite3
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / 'data/processed'


def main():
    checks = []

    def check(name, condition, detail):
        checks.append({'check': name, 'passed': bool(condition), 'evidence': str(detail)})

    with sqlite3.connect(PROC / 'olist.db') as con:
        sql = pd.read_sql_query('SELECT * FROM v_delivered_orders ORDER BY order_id', con)
        raw_orders = pd.read_sql_query('SELECT * FROM orders', con)
        raw_items = pd.read_sql_query('SELECT * FROM order_items', con)
        raw_customers = pd.read_sql_query('SELECT * FROM customers', con)
        raw_reviews = pd.read_sql_query('SELECT order_id, review_score FROM order_reviews', con)
        sql_items = pd.read_sql_query('SELECT * FROM v_items', con)
        check('Raw primary keys', raw_orders.order_id.is_unique and raw_customers.customer_id.is_unique
              and not raw_items.duplicated(['order_id','order_item_id']).any(), 'orders, customers and order/item keys unique')
        check('Order-item foreign keys', raw_items.order_id.isin(raw_orders.order_id).all(), 'Every item has an order')
        check('Order-customer foreign keys', raw_orders.customer_id.isin(raw_customers.customer_id).all(), 'Every order has a customer')
        check('Review score range', raw_reviews.review_score.between(1,5).all(), 'All source scores are between 1 and 5')

    clean = pd.read_csv(PROC / 'orders_clean.csv')
    o = clean[(clean.order_status == 'delivered') & clean.delivery_days.notna()].sort_values('order_id').reset_index(drop=True)
    check('Delivered population', sql.order_id.tolist() == o.order_id.tolist(), f'{len(o):,} orders')
    check('One row per clean order', clean.order_id.is_unique, f'{len(clean):,} clean orders')
    for col in ['revenue','freight','review_score','days_vs_estimate','is_late']:
        check(f'SQL / Python {col}', np.allclose(sql[col],o[col],equal_nan=True,atol=1e-8), 'Order-level reconciliation')
    check('Delivery duration rounding', np.allclose(sql.delivery_days, o.delivery_days,atol=.051), 'SQL rounds to one decimal day')
    check('Revenue source tie-out', np.isclose(raw_items.loc[raw_items.order_id.isin(o.order_id),'price'].sum(),o.revenue.sum()), f'R$ {o.revenue.sum():,.2f}; freight excluded')
    check('Analysis dates', o.purchase_date.between('2017-01-01','2018-08-31').all(), 'Jan 2017 through Aug 2018')
    check('Review missingness preserved',
          set(o.loc[o.review_score.isna(),'order_id']) == set(o.loc[~o.order_id.isin(raw_reviews.order_id),'order_id']),
          f'{o.review_score.isna().sum()} orders without source reviews remain missing')
    rfm = pd.read_csv(PROC / 'customers_rfm.csv')
    check('RFM customer uniqueness', rfm.customer_unique_id.is_unique and set(rfm.customer_unique_id)==set(o.customer_unique_id), f'{len(rfm):,} delivered customers')
    check('RFM revenue reconciliation', np.isclose(rfm.monetary.sum(),o.revenue.sum()), 'Customer spend sums to delivered merchandise sales')
    seg = pd.read_csv(PROC / 'sql_results/04_customers__rfm_segments.csv').set_index('segment')
    counts = rfm.groupby('segment').size().reindex(seg.index)
    check('SQL / Python RFM segments', np.array_equal(seg.customers,counts), counts.to_dict())
    cohorts = pd.read_csv(PROC / 'sql_results/04_customers__cohort_retention.csv')
    o['month'] = pd.to_datetime(o.purchase_date).dt.to_period('M')
    first = o.groupby('customer_unique_id')['month'].min()
    activity = o[['customer_unique_id','month']].drop_duplicates()
    activity['cohort'] = activity.customer_unique_id.map(first)
    activity['age'] = activity.month.astype('int64')-activity.cohort.astype('int64')
    expected = []
    for row in cohorts.itertuples():
        for age in [1,2,3,6]:
            coh = pd.Period(row.cohort)
            actual = getattr(row,f'm{age}_pct')
            if coh+age>pd.Period('2018-08'):
                expected.append(pd.isna(actual))
            else:
                n = activity.loc[(activity.cohort==coh)&(activity.age==age),'customer_unique_id'].nunique()
                expected.append(np.isclose(actual,round(100*n/row.cohort_size,2)))
    check('Cohort rates and observation windows', all(expected), 'All 80 SQL retention cells match pandas; future months stay blank')

    facts = pd.read_csv(PROC / 'powerbi/fact_orders.csv')
    items = pd.read_csv(PROC / 'powerbi/fact_order_items.csv')
    cust = pd.read_csv(PROC / 'powerbi/dim_customer.csv')
    eligible = facts[facts.is_delivered==1]
    check('Power BI delivered population', set(eligible.order_id)==set(o.order_id), f'{len(eligible):,} eligible orders')
    check('Power BI customer relationship', cust.customer_unique_id.is_unique and facts.customer_unique_id.isin(cust.customer_unique_id).all(), 'Unique dimension; no orphan customer keys')
    check('Power BI item relationship', facts.order_id.is_unique and items.order_id.isin(facts.order_id).all(), 'One-to-many order/item relationship')
    check('Power BI item sales', np.isclose(items.loc[items.order_id.isin(eligible.order_id),'price'].sum(),o.revenue.sum()), 'Category sales sum to order sales')
    check('Power BI state keys', facts.customer_state.isin(pd.read_csv(PROC / 'powerbi/dim_state.csv').state_code).all(), 'All state keys mapped')
    check('Power BI date keys', facts.purchase_date.isin(pd.read_csv(PROC / 'powerbi/dim_date.csv').date).all(), 'All purchase dates mapped')
    kpi = pd.read_csv(PROC / 'sql_results/03_sales__kpis.csv').iloc[0]
    check('Published SQL KPI totals', kpi.orders==len(o) and kpi.customers==o.customer_unique_id.nunique() and abs(kpi.revenue-o.revenue.sum())<.51, kpi.to_dict())

    category = sql_items.drop_duplicates(['category','order_id']).dropna(subset=['review_score'])
    means = category.groupby('category').review_score.mean().round(2)
    result = pd.read_csv(PROC/'sql_results/06_reviews__worst_reviewed_categories.csv').set_index('category')
    check('Category reviews use order grain', np.allclose(means.reindex(result.index),result.avg_review), 'Independent pandas aggregation matches all reported categories')
    seller_means = sql_items.drop_duplicates(['seller_id','order_id']).groupby('seller_id').review_score.mean().round(2)
    result = pd.read_csv(PROC/'sql_results/08_sellers__problem_sellers.csv').set_index('seller_id')
    check('Seller reviews use order grain', np.allclose(seller_means.reindex(result.index),result.avg_review), 'Independent pandas aggregation matches all reported sellers')
    stats = {'orders':len(o),'customers':o.customer_unique_id.nunique(),'revenue':round(o.revenue.sum(),2),
             'avg_order_value':round(o.revenue.mean(),2),'avg_review':round(o.review_score.mean(),2),
             'late_pct':round(100*o.is_late.mean(),2),'repeat_customer_pct':round(100*rfm.frequency.gt(1).mean(),2)}
    report = {'checked_on':str(date(2026,11,5)), 'checks':checks,'metrics':stats,
              'limitations':['Power BI Desktop DAX execution and rendering not verified: UI helper failed to initialize.',
                             'Excel native application checks are reported separately.']}
    target = ROOT / 'docs/validation_results.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(report,indent=2,default=str)+'\n',encoding='utf-8')
    for item in checks:
        print(('PASS' if item['passed'] else 'FAIL') + ': ' + item['check'])
    print(stats)
    failed = [x['check'] for x in checks if not x['passed']]
    if failed:
        raise SystemExit('Failed checks: ' + ', '.join(failed))
    print(f'PASS: {len(checks)} checks. Report: docs/validation_results.json')


if __name__ == '__main__':
    main()
