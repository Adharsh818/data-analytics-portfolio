-- Q6. Sellers

-- name: seller_concentration
WITH s AS (
    SELECT seller_id,
           SUM(price) AS revenue,
           NTILE(10) OVER (ORDER BY SUM(price) DESC) AS decile
    FROM v_items
    GROUP BY seller_id
)
SELECT decile,
       COUNT(*)               AS sellers,
       ROUND(SUM(revenue), 0) AS revenue,
       ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 1) AS pct_revenue
FROM s
GROUP BY decile
ORDER BY decile;

-- name: problem_sellers
-- High-volume sellers with poor reviews: candidates for a seller-quality program
SELECT i.seller_id,
       sl.seller_state,
       COUNT(DISTINCT i.order_id)       AS orders,
       ROUND(SUM(i.price), 0)           AS revenue,
       ROUND(AVG(i.review_score), 2)    AS avg_review,
       ROUND(100.0 * AVG(i.is_late), 1) AS late_pct
FROM v_items i
JOIN sellers sl USING (seller_id)
GROUP BY i.seller_id
HAVING COUNT(DISTINCT i.order_id) >= 100
ORDER BY avg_review
LIMIT 10;
