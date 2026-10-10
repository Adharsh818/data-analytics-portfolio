-- Q3. Delivery performance

-- name: delivery_summary
SELECT ROUND(AVG(delivery_days), 1)                                    AS avg_delivery_days,
       ROUND(100.0 * AVG(is_late), 1)                                  AS late_pct,
       ROUND(AVG(CASE WHEN is_late = 1 THEN days_vs_estimate END), 1)  AS avg_days_late_when_late,
       ROUND(AVG(CASE WHEN is_late = 0 THEN -days_vs_estimate END), 1) AS avg_days_early_when_on_time
FROM v_delivered_orders;

-- name: late_by_state
SELECT customer_state,
       COUNT(*)                       AS orders,
       ROUND(AVG(delivery_days), 1)   AS avg_delivery_days,
       ROUND(100.0 * AVG(is_late), 1) AS late_pct
FROM v_delivered_orders
GROUP BY customer_state
HAVING COUNT(*) >= 500
ORDER BY late_pct DESC;

-- name: late_by_month
SELECT purchase_month,
       COUNT(*)                       AS orders,
       ROUND(AVG(delivery_days), 1)   AS avg_delivery_days,
       ROUND(100.0 * AVG(is_late), 1) AS late_pct
FROM v_delivered_orders
GROUP BY purchase_month
ORDER BY purchase_month;
