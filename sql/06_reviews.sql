-- Q4. Customer satisfaction

-- name: review_by_lateness
SELECT CASE WHEN days_vs_estimate <= 0 THEN '1. On time / early'
            WHEN days_vs_estimate <= 3 THEN '2. 1-3 days late'
            WHEN days_vs_estimate <= 7 THEN '3. 4-7 days late'
            ELSE '4. 8+ days late' END                                  AS delivery_bucket,
       COUNT(*)                                                         AS orders,
       ROUND(AVG(review_score), 2)                                      AS avg_review,
       ROUND(100.0 * AVG(CASE WHEN review_score <= 2 THEN 1.0 ELSE 0 END), 1) AS pct_1_2_star
FROM v_delivered_orders
WHERE review_score IS NOT NULL
GROUP BY delivery_bucket
ORDER BY delivery_bucket;

-- name: review_distribution
SELECT CAST(ROUND(review_score) AS INT) AS stars,
       COUNT(*)                         AS orders,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM v_delivered_orders
WHERE review_score IS NOT NULL
GROUP BY stars
ORDER BY stars;

-- name: worst_reviewed_categories
SELECT category,
       COUNT(DISTINCT order_id)       AS orders,
       ROUND(AVG(review_score), 2)    AS avg_review,
       ROUND(100.0 * AVG(is_late), 1) AS late_pct
FROM v_items
WHERE review_score IS NOT NULL
GROUP BY category
HAVING COUNT(DISTINCT order_id) >= 500
ORDER BY avg_review
LIMIT 10;
