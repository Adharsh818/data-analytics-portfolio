# Retail operations review

**Question:** Where should an online retail team focus its next investigation?

**Scope:** 96,203 delivered Olist orders purchased January 2017–August 2018.
Sales are item prices in R$, excluding freight. This is a public-data portfolio study.

## Findings

Delivered merchandise sales total R$13.18M, with R$137 average order value.
November 2017 sales were 52.4% above October. Monthly sales in 2018 range from
R$0.83M to R$0.98M; a peak month alone is not evidence of sustainable growth.

Delivery reliability is a useful investigation priority: 6.8% of eligible orders
arrived after the promised calendar date. Among states with at least 500 orders,
MA has 17.5% late deliveries, CE 13.8% and RJ 12.1%, compared with SP at 4.5%.
Rates should be reviewed alongside order counts; a high rate in a small market
may represent fewer customers than a moderate rate in a large one.

On-time orders average 4.29 review stars, compared with 1.70 for orders 8+ days late.
79.2% of reviewed orders in the latter group have an order-average score of 2 or lower.
These differences support investigation, but do not prove late delivery caused the
review difference. Product quality, seller, location and other factors may contribute.

About 3.0% of customers place more than one delivered order in the observed window.
Monthly cohort retention is under 1% in each observed later month. Olist is a
marketplace; purchases elsewhere and before the window are not observed, and recent
cohorts have shorter follow-up. This is not a churn estimate for a grocery chain.

## Proposed follow-up

| Priority | Proposed team | First action | Measure | Evidence needed before investing |
|---|---|---|---|---|
| 1 | Fulfilment / operations | Review late-order volume and seller dispatch versus carrier transit in MA, CE and RJ. | Late orders / orders with known delivery promise; review coverage and score alongside it. | Carrier/service-level data, dispatch constraints and cost of changes. |
| 2 | Customer / CRM analytics | Test a second-purchase offer for a defined recent high-value group, using a random control group. | 60-day repeat purchase rate with equal follow-up; incremental contribution after offer costs. | Consent, campaign exposure and cost/margin data. |
| 3 | Seller operations | Review high-volume sellers with poor order-level review averages. | Reviewed order count, average score and late rate. | Complaints, item-level causes and carrier responsibility before attributing blame. |
| 4 | Commercial planning | Compare peak-month demand and delivery outcomes before the next peak. | Purchase-month sales and late rate. | Promotion calendar, daily demand and capacity data before claiming promotion impact. |

These are proposed actions, not interventions performed or savings achieved.

## Relevance to retail analytics

The work demonstrates transaction joins, consistent KPI definitions, geographic
performance comparisons, data quality checks and recommendations for operational teams.
Those methods transfer to retail. For a store-led business, the next dataset should add
store/SKU inventory snapshots, replenishment, product costs and promotions so that
availability, inventory turns, basket attachment and margin can be measured properly.

Evidence: [sales](../sql/03_sales.sql), [delivery](../sql/05_delivery.sql),
[reviews](../sql/06_reviews.sql), [customers](../sql/04_customers.sql),
[validation](validation_results.json). Source: [Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
