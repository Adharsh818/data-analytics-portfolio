# Data dictionary and measurement rules

Source: [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
The raw dataset covers 2016–2018. This project restricts purchase dates to
`2017-01-01 <= timestamp < 2018-09-01` for a consistent 20-month window.

## Source tables

| Table | One row represents | Join key / caution |
|---|---|---|
| orders | An order | `order_id` unique; status and timestamps. |
| customers | An order-specific customer record | `customer_id` unique; group people by `customer_unique_id`. |
| order_items | An order line | `(order_id, order_item_id)` unique; an order may have several sellers/categories. |
| order_payments | A payment record | An order may have several payments; aggregate before joining to items. |
| order_reviews | A review record | `review_id` is not unique; average scores per order. |
| products | A product | `product_id` unique; missing categories become `unknown`. |
| sellers | A seller | `seller_id` unique. |
| category_translation | A category translation | Preserve `pc_gamer`; map long kitchen category manually. |
| geolocation | A ZIP/location observation | ZIP is not unique; loaded/profiled but not joined to orders. |

## Clean tables and Power BI

| Table / view | Grain | Population |
|---|---|---|
| `v_orders`, `orders_clean.csv`, `fact_orders` | One order with at least one item | Analysis window, all statuses; 98,353 rows. |
| `v_delivered_orders` | One eligible delivered order | Delivered and known delivery timestamp; 96,203 rows. |
| `v_items` | One item from an eligible order | Revenue by category and seller. |
| `order_items_clean.csv`, `fact_order_items` | One item in a clean-window order | All statuses; filter through eligible `fact_orders` for sales. |
| `customers_rfm.csv` | One person with an eligible order | 93,096 customers, full-window snapshot. |
| `dim_customer` | One observed clean-window person | 95,121 customers; people with no eligible order have a separate label. |
| `dim_state` | One Brazilian state | 27 rows, names and regions. |
| `dim_date` | One calendar day | 608 dates, January 2017 through August 2018. |

## Metrics

| Metric | Definition / denominator |
|---|---|
| Delivered orders | Count of eligible order IDs; delivered status with known actual delivery date. |
| Revenue / merchandise sales | Sum of eligible item prices; no freight, refund or cost deduction. |
| AOV | Merchandise sales / delivered orders. |
| Freight share | Sum of freight / sum of merchandise sales; not average of order-level ratios. |
| Customers | Distinct `customer_unique_id` with eligible purchases in selected context. |
| Delivery days | Actual delivery timestamp minus purchase timestamp, in fractional days. SQL rounds to 1 decimal. |
| Days versus estimate | Actual calendar delivery date minus estimated calendar date. |
| Late rate | Late orders / orders with known actual and estimated delivery dates. |
| Average review | Average of per-order review averages; exclude missing reviews. |
| Bad review share | Reviewed orders with order-average score <= 2 / all reviewed orders. |
| Repeat customer share | Customers with 2+ eligible orders / customers with 1+ eligible orders in selected window. |
| Monthly retention | Cohort customers ordering in month N / cohort size. First purchase means first observed in window. |
| Category/seller reviews | Each order counts once within a category or seller, even with several lines there. |
| Payment mix | Share of source payment value, including freight; multiple payment types may occur per order. |

The largest-value payment record supplies the order-level `payment_type` slicer;
ties use payment sequence. `installments` is the maximum installment count on the order.
Payment-record averages in SQL are not item-price AOV and do not demonstrate that
installments increase spending.

## RFM rules

Recency is days since the most recent eligible purchase, using the day after the latest
observed purchase as the snapshot date. Monetary is delivered merchandise spend.
The cumulative percentile rank of recency and monetary determines each quintile;
tied values remain together, so groups need not contain equal customer counts.
SQL uses `CUME_DIST`; pandas uses `rank(method='max', pct=True)`. Monetary ranks use cents.
Recency scores are reversed so recent customers score higher. Frequency scores are
1 for one order, 4 for two and 5 for three or more; quintiles are unsuitable when
about 97% order once.

Segments are assigned in order: repeat/high monetary → Champions; other repeat →
Loyal; high recency/high monetary → New high-value; other high recency → New low-value;
low recency/high monetary → At risk high-value; otherwise Hibernating.
`New` means recent in this scoring rule, not verified acquisition. `At risk` is a
descriptive label, not a validated churn prediction.

Power BI keeps full-window labels fixed when date/state slicers change. Customer
counts and revenue respond to slicers; segment membership does not.
