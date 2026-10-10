-- Q1. Sales performance

-- name: kpis
SELECT COUNT(*)                           AS orders,
       COUNT(DISTINCT customer_unique_id) AS customers,
       ROUND(SUM(revenue), 0)             AS revenue,
       ROUND(SUM(revenue) / COUNT(*), 2)  AS avg_order_value,
       ROUND(AVG(review_score), 2)        AS avg_review,
       ROUND(100.0 * AVG(is_late), 1)     AS late_pct
FROM v_delivered_orders;

-- name: monthly_revenue
SELECT purchase_month,
       COUNT(*)                          AS orders,
       ROUND(SUM(revenue), 0)            AS revenue,
       ROUND(SUM(revenue) / COUNT(*), 2) AS avg_order_value,
       ROUND(100.0 * (SUM(revenue) - LAG(SUM(revenue)) OVER (ORDER BY purchase_month))
             / LAG(SUM(revenue)) OVER (ORDER BY purchase_month), 1) AS mom_growth_pct
FROM v_delivered_orders
GROUP BY purchase_month
ORDER BY purchase_month;

-- name: top_categories
SELECT category,
       COUNT(DISTINCT order_id) AS orders,
       ROUND(SUM(price), 0)     AS revenue,
       ROUND(100.0 * SUM(price) / SUM(SUM(price)) OVER (), 1) AS revenue_share_pct,
       ROUND(100.0 * SUM(SUM(price)) OVER (ORDER BY SUM(price) DESC)
             / SUM(SUM(price)) OVER (), 1) AS cumulative_share_pct
FROM v_items
GROUP BY category
ORDER BY revenue DESC
LIMIT 15;

-- name: revenue_by_state
SELECT customer_state,
       COUNT(*)                                AS orders,
       ROUND(SUM(revenue), 0)                  AS revenue,
       ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 1) AS revenue_share_pct,
       ROUND(100.0 * AVG(freight / revenue), 1) AS freight_as_pct_of_price
FROM v_delivered_orders
GROUP BY customer_state
ORDER BY revenue DESC;

-- name: sales_by_weekday
SELECT CASE STRFTIME('%w', purchase_date)
         WHEN '0' THEN 'Sun' WHEN '1' THEN 'Mon' WHEN '2' THEN 'Tue' WHEN '3' THEN 'Wed'
         WHEN '4' THEN 'Thu' WHEN '5' THEN 'Fri' ELSE 'Sat' END AS weekday,
       COUNT(*)               AS orders,
       ROUND(SUM(revenue), 0) AS revenue
FROM v_delivered_orders
GROUP BY STRFTIME('%w', purchase_date)
ORDER BY STRFTIME('%w', purchase_date);
