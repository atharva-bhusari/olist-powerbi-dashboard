# Data Dictionary — processed star-schema tables

These are the tables emitted by `src/prep_data.py` into `data/processed/`
(as both `.csv` and `.parquet`). Row counts below are from the current
build against the full Olist raw CSVs.

## fct_order_items (fact — grain: one row per order line item) — 112,650 rows

| Column | Type | Description |
|---|---|---|
| order_id | VARCHAR | FK → dim_orders |
| product_id | VARCHAR | FK → dim_products |
| seller_id | VARCHAR | FK → dim_sellers |
| order_date | DATE | FK → dim_date (order purchase date) |
| price | DOUBLE | Item price (BRL) |
| freight_value | DOUBLE | Freight charged for the item (BRL) |

## dim_orders (grain: one row per order) — 99,441 rows

| Column | Type | Description |
|---|---|---|
| order_id | VARCHAR | PK |
| customer_id | VARCHAR | FK → dim_customers |
| order_status | VARCHAR | delivered, shipped, canceled, ... |
| purchase_ts | TIMESTAMP | Order placed |
| delivered_ts | TIMESTAMP | Delivered to customer (NULL if not yet delivered) |
| estimated_ts | TIMESTAMP | Promised delivery date |
| delivery_days | BIGINT | delivered_ts − purchase_ts, in days (NULL if not delivered) |
| estimated_days | BIGINT | estimated_ts − purchase_ts, in days |
| is_late | BOOLEAN | delivered_ts > estimated_ts (NULL if not delivered) |
| review_score | BIGINT | 1–5, one per order (latest review by review_creation_date if multiple) |

## dim_customers — 99,441 rows

| Column | Type | Description |
|---|---|---|
| customer_id | VARCHAR | PK |
| customer_state | VARCHAR | Brazilian state (2-letter) |
| customer_city | VARCHAR | City |

## dim_products — 32,951 rows

| Column | Type | Description |
|---|---|---|
| product_id | VARCHAR | PK |
| product_category | VARCHAR | Category (English, via translation table; `'unknown'` if missing — 623 rows) |
| product_weight_g | BIGINT | Weight in grams |

## dim_sellers — 3,095 rows

| Column | Type | Description |
|---|---|---|
| seller_id | VARCHAR | PK |
| seller_state | VARCHAR | Brazilian state (2-letter) |
| seller_city | VARCHAR | City |

## dim_date — 774 rows

Generated across the full range of `order_purchase_timestamp` dates (one row per calendar day).

| Column | Type | Description |
|---|---|---|
| date | DATE | PK |
| year | BIGINT | |
| month | BIGINT | 1–12 |
| month_name | VARCHAR | Full month name (e.g. "January") |
| quarter | BIGINT | 1–4 |
