-- Olist Brazilian E-commerce: table schema (SQLite)
-- Source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

DROP TABLE IF EXISTS customers;
CREATE TABLE customers (
    customer_id              TEXT PRIMARY KEY,  -- one per order
    customer_unique_id       TEXT NOT NULL,     -- the real person
    customer_zip_code_prefix TEXT,
    customer_city            TEXT,
    customer_state           TEXT
);

DROP TABLE IF EXISTS sellers;
CREATE TABLE sellers (
    seller_id              TEXT PRIMARY KEY,
    seller_zip_code_prefix TEXT,
    seller_city            TEXT,
    seller_state           TEXT
);

DROP TABLE IF EXISTS products;
CREATE TABLE products (
    product_id                 TEXT PRIMARY KEY,
    product_category_name      TEXT,
    product_name_lenght        INTEGER,  -- original column names keep the source typos
    product_description_lenght INTEGER,
    product_photos_qty         INTEGER,
    product_weight_g           REAL,
    product_length_cm          REAL,
    product_height_cm          REAL,
    product_width_cm           REAL
);

DROP TABLE IF EXISTS category_translation;
CREATE TABLE category_translation (
    product_category_name         TEXT PRIMARY KEY,
    product_category_name_english TEXT
);

DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
    order_id                      TEXT PRIMARY KEY,
    customer_id                   TEXT REFERENCES customers(customer_id),
    order_status                  TEXT,
    order_purchase_timestamp      TEXT,
    order_approved_at             TEXT,
    order_delivered_carrier_date  TEXT,
    order_delivered_customer_date TEXT,
    order_estimated_delivery_date TEXT
);

DROP TABLE IF EXISTS order_items;
CREATE TABLE order_items (
    order_id            TEXT REFERENCES orders(order_id),
    order_item_id       INTEGER,
    product_id          TEXT REFERENCES products(product_id),
    seller_id           TEXT REFERENCES sellers(seller_id),
    shipping_limit_date TEXT,
    price               REAL,
    freight_value       REAL,
    PRIMARY KEY (order_id, order_item_id)
);

DROP TABLE IF EXISTS order_payments;
CREATE TABLE order_payments (
    order_id             TEXT REFERENCES orders(order_id),
    payment_sequential   INTEGER,
    payment_type         TEXT,
    payment_installments INTEGER,
    payment_value        REAL
);

DROP TABLE IF EXISTS order_reviews;
CREATE TABLE order_reviews (
    review_id               TEXT,  -- not unique in the source data
    order_id                TEXT REFERENCES orders(order_id),
    review_score            INTEGER,
    review_comment_title    TEXT,
    review_comment_message  TEXT,
    review_creation_date    TEXT,
    review_answer_timestamp TEXT
);

DROP TABLE IF EXISTS geolocation;
CREATE TABLE geolocation (
    geolocation_zip_code_prefix TEXT,
    geolocation_lat             REAL,
    geolocation_lng             REAL,
    geolocation_city            TEXT,
    geolocation_state           TEXT
);
