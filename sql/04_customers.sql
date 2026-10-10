-- Q2. Customers: repeat purchase, cohorts, RFM

-- name: repeat_rate
WITH per_customer AS (
    SELECT customer_unique_id, COUNT(*) AS n_orders, SUM(revenue) AS spend
    FROM v_delivered_orders
    GROUP BY customer_unique_id
)
SELECT CASE WHEN n_orders = 1 THEN '1 order'
            WHEN n_orders = 2 THEN '2 orders'
            ELSE '3+ orders' END                          AS segment,
       COUNT(*)                                            AS customers,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)  AS pct_customers,
       ROUND(100.0 * SUM(spend) / SUM(SUM(spend)) OVER (), 2) AS pct_revenue
FROM per_customer
GROUP BY segment
ORDER BY segment;

-- name: cohort_retention
-- Share of each monthly cohort that ordered again 1, 2, 3 and 6 months after their first order
WITH first AS (
    SELECT customer_unique_id, MIN(purchase_month) AS cohort
    FROM v_delivered_orders
    GROUP BY customer_unique_id
),
activity AS (
    SELECT DISTINCT f.cohort, o.customer_unique_id,
           (CAST(SUBSTR(o.purchase_month, 1, 4) AS INT) - CAST(SUBSTR(f.cohort, 1, 4) AS INT)) * 12
         + (CAST(SUBSTR(o.purchase_month, 6, 2) AS INT) - CAST(SUBSTR(f.cohort, 6, 2) AS INT)) AS month_n
    FROM v_delivered_orders o
    JOIN first f USING (customer_unique_id)
),
counts AS (
    SELECT cohort,
           COUNT(DISTINCT CASE WHEN month_n = 0 THEN customer_unique_id END) AS cohort_size,
           COUNT(DISTINCT CASE WHEN month_n = 1 THEN customer_unique_id END) AS m1,
           COUNT(DISTINCT CASE WHEN month_n = 2 THEN customer_unique_id END) AS m2,
           COUNT(DISTINCT CASE WHEN month_n = 3 THEN customer_unique_id END) AS m3,
           COUNT(DISTINCT CASE WHEN month_n = 6 THEN customer_unique_id END) AS m6
    FROM activity
    GROUP BY cohort
)
SELECT cohort, cohort_size,
       ROUND(100.0 * m1 / cohort_size, 2) AS m1_pct,
       ROUND(100.0 * m2 / cohort_size, 2) AS m2_pct,
       ROUND(100.0 * m3 / cohort_size, 2) AS m3_pct,
       ROUND(100.0 * m6 / cohort_size, 2) AS m6_pct
FROM counts
ORDER BY cohort;

-- name: rfm_segments
-- Recency and Monetary scored 1-5 with NTILE. Frequency is scored by order count instead,
-- because ~97% of customers bought once and quintiles on frequency would be meaningless.
WITH ref AS (SELECT DATE(MAX(purchase_date), '+1 day') AS d FROM v_delivered_orders),
base AS (
    SELECT customer_unique_id,
           CAST(JULIANDAY((SELECT d FROM ref)) - JULIANDAY(MAX(purchase_date)) AS INT) AS recency_days,
           COUNT(*)     AS frequency,
           SUM(revenue) AS monetary
    FROM v_delivered_orders
    GROUP BY customer_unique_id
),
scored AS (
    SELECT *,
           NTILE(5) OVER (ORDER BY recency_days DESC) AS r,
           CASE WHEN frequency >= 3 THEN 5 WHEN frequency = 2 THEN 4 ELSE 1 END AS f,
           NTILE(5) OVER (ORDER BY monetary) AS m
    FROM base
)
SELECT CASE
         WHEN f >= 4 AND m >= 4 THEN 'Champions'
         WHEN f >= 4            THEN 'Loyal'
         WHEN r >= 4 AND m >= 4 THEN 'New high-value'
         WHEN r >= 4            THEN 'New low-value'
         WHEN r <= 2 AND m >= 4 THEN 'At risk high-value'
         ELSE 'Hibernating'
       END                                  AS segment,
       COUNT(*)                             AS customers,
       ROUND(AVG(recency_days), 0)          AS avg_recency_days,
       ROUND(AVG(frequency), 2)             AS avg_orders,
       ROUND(AVG(monetary), 2)              AS avg_spend,
       ROUND(100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 1) AS pct_revenue
FROM scored
GROUP BY segment
ORDER BY pct_revenue DESC;
