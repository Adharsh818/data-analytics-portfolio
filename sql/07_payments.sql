-- Q5. Payments

-- name: payment_mix
SELECT p.payment_type,
       COUNT(DISTINCT p.order_id)     AS orders,
       ROUND(100.0 * SUM(p.payment_value) / SUM(SUM(p.payment_value)) OVER (), 1) AS pct_value,
       ROUND(AVG(p.payment_value), 2) AS avg_payment
FROM order_payments p
JOIN v_delivered_orders o ON o.order_id = p.order_id
WHERE p.payment_type <> 'not_defined'
GROUP BY p.payment_type
ORDER BY orders DESC;

-- name: installments_vs_value
SELECT CASE WHEN payment_installments <= 1 THEN '1 (single)'
            WHEN payment_installments <= 3 THEN '2-3'
            WHEN payment_installments <= 6 THEN '4-6'
            ELSE '7+' END              AS installments,
       COUNT(*)                        AS payments,
       ROUND(AVG(payment_value), 2)    AS avg_payment_value
FROM order_payments p
JOIN v_delivered_orders o ON o.order_id = p.order_id
WHERE p.payment_type = 'credit_card'
GROUP BY installments
ORDER BY MIN(payment_installments);
