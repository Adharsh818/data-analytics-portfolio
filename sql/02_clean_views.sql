-- Cleaned, analysis-ready views built on the raw tables.
-- Decisions:
--   * Analysis window is Jan 2017 to Aug 2018 (full months; 2016 and Sep-Oct 2018 are sparse).
--   * Revenue = item price (excludes freight). Freight is reported separately.
--   * Revenue counts only delivered orders, so canceled/unavailable orders don't inflate sales.
--   * Customers are identified by customer_unique_id (customer_id changes on every order).

DROP VIEW IF EXISTS v_products;
CREATE VIEW v_products AS
SELECT
    p.product_id,
    COALESCE(t.product_category_name_english,
             CASE p.product_category_name
                 WHEN 'pc_gamer' THEN 'pc_gamer'
                 WHEN 'portateis_cozinha_e_preparadores_de_alimentos' THEN 'portable_kitchen_appliances'
             END,
             'unknown') AS category,
    p.product_weight_g
FROM products p
LEFT JOIN category_translation t USING (product_category_name);

DROP VIEW IF EXISTS v_order_reviews;
CREATE VIEW v_order_reviews AS   -- a few orders have 2+ reviews: average them
SELECT order_id, AVG(review_score) AS review_score
FROM order_reviews
GROUP BY order_id;

DROP VIEW IF EXISTS v_orders;
CREATE VIEW v_orders AS
WITH items AS (
    SELECT order_id,
           COUNT(*)           AS n_items,
           SUM(price)         AS revenue,
           SUM(freight_value) AS freight
    FROM order_items
    GROUP BY order_id
)
SELECT
    o.order_id,
    c.customer_unique_id,
    c.customer_state,
    o.order_status,
    DATE(o.order_purchase_timestamp)              AS purchase_date,
    STRFTIME('%Y-%m', o.order_purchase_timestamp) AS purchase_month,
    i.n_items,
    i.revenue,
    i.freight,
    r.review_score,
    ROUND(JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp), 1) AS delivery_days,
    CASE WHEN o.order_delivered_customer_date IS NULL THEN NULL
         WHEN DATE(o.order_delivered_customer_date) > DATE(o.order_estimated_delivery_date) THEN 1
         ELSE 0 END AS is_late,
    CAST(JULIANDAY(DATE(o.order_delivered_customer_date))
       - JULIANDAY(DATE(o.order_estimated_delivery_date)) AS INTEGER) AS days_vs_estimate
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN items i     ON i.order_id = o.order_id      -- drops 775 orders that have no items
LEFT JOIN v_order_reviews r ON r.order_id = o.order_id
WHERE o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp <  '2018-09-01';

DROP VIEW IF EXISTS v_delivered_orders;
CREATE VIEW v_delivered_orders AS
SELECT * FROM v_orders
WHERE order_status = 'delivered' AND delivery_days IS NOT NULL;

DROP VIEW IF EXISTS v_items;
CREATE VIEW v_items AS
SELECT oi.order_id, oi.product_id, oi.seller_id, oi.price, oi.freight_value,
       p.category, o.purchase_month, o.customer_state, o.review_score, o.is_late
FROM order_items oi
JOIN v_delivered_orders o ON o.order_id = oi.order_id
JOIN v_products p         ON p.product_id = oi.product_id;
