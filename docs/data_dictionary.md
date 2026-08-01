# Data Dictionary — processed star-schema tables

These are the tables emitted by `src/prep_data.py` into `data/processed/`.
Filled in fully during the data-prep phase.

## fct_order_items (fact — grain: one row per order line item)

| Column | Type | Description |
|---|---|---|
| order_id | string | FK → dim_orders |
| product_id | string | FK → dim_products |
| seller_id | string | FK → dim_sellers |
| order_date | date | FK → dim_date (order purchase date) |
| price | decimal | Item price (BRL) |
| freight_value | decimal | Freight charged for the item (BRL) |

## dim_orders (grain: one row per order)

| Column | Type | Description |
|---|---|---|
| order_id | string | PK |
| customer_id | string | FK → dim_customers |
| order_status | string | delivered, shipped, canceled, ... |
| purchase_ts | timestamp | Order placed |
| delivered_customer_ts | timestamp | Delivered to customer |
| estimated_delivery_ts | timestamp | Promised delivery date |
| review_score | int | 1–5 (from reviews, one per order) |

## dim_customers

| Column | Type | Description |
|---|---|---|
| customer_id | string | PK |
| customer_state | string | Brazilian state (2-letter) |
| customer_city | string | City |

## dim_products

| Column | Type | Description |
|---|---|---|
| product_id | string | PK |
| product_category | string | Category (English) |
| product_weight_g | int | Weight in grams |

## dim_sellers

| Column | Type | Description |
|---|---|---|
| seller_id | string | PK |
| seller_state | string | Brazilian state (2-letter) |
| seller_city | string | City |

## dim_date

| Column | Type | Description |
|---|---|---|
| date | date | PK |
| year | int | |
| month | int | |
| month_name | string | |
| quarter | int | |
