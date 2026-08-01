"""
DuckDB data-prep pipeline: raw Olist CSVs -> star-schema tables.

Reads data/raw/*.csv, builds the six star-schema tables described in
plan.md section 3, and writes each to data/processed/ as both .csv and
.parquet. Safe to re-run: every output file is fully overwritten, so
there is no accumulation of duplicate rows across runs.
"""

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"


def path(name: str) -> str:
    return str((RAW / name).as_posix())


def build(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(f"""
        CREATE OR REPLACE VIEW raw_orders AS
            SELECT * FROM read_csv_auto('{path("olist_orders_dataset.csv")}');
        CREATE OR REPLACE VIEW raw_order_items AS
            SELECT * FROM read_csv_auto('{path("olist_order_items_dataset.csv")}');
        CREATE OR REPLACE VIEW raw_products AS
            SELECT * FROM read_csv_auto('{path("olist_products_dataset.csv")}');
        CREATE OR REPLACE VIEW raw_customers AS
            SELECT * FROM read_csv_auto('{path("olist_customers_dataset.csv")}');
        CREATE OR REPLACE VIEW raw_sellers AS
            SELECT * FROM read_csv_auto('{path("olist_sellers_dataset.csv")}');
        CREATE OR REPLACE VIEW raw_reviews AS
            SELECT * FROM read_csv_auto('{path("olist_order_reviews_dataset.csv")}');
        CREATE OR REPLACE VIEW raw_translation AS
            SELECT * FROM read_csv_auto('{path("product_category_name_translation.csv")}');
    """)

    # --- dim_customers -----------------------------------------------------
    con.execute("""
        CREATE OR REPLACE TABLE dim_customers AS
        SELECT DISTINCT
            customer_id,
            customer_state,
            customer_city
        FROM raw_customers;
    """)

    # --- dim_sellers ---------------------------------------------------------
    con.execute("""
        CREATE OR REPLACE TABLE dim_sellers AS
        SELECT DISTINCT
            seller_id,
            seller_state,
            seller_city
        FROM raw_sellers;
    """)

    # --- dim_products (category translated to English, nulls -> 'unknown') --
    con.execute("""
        CREATE OR REPLACE TABLE dim_products AS
        SELECT
            p.product_id,
            COALESCE(t.product_category_name_english, 'unknown') AS product_category,
            p.product_weight_g
        FROM raw_products p
        LEFT JOIN raw_translation t
            ON p.product_category_name = t.product_category_name;
    """)

    # --- dim_date: generated across the full order-date range --------------
    con.execute("""
        CREATE OR REPLACE TABLE dim_date AS
        WITH bounds AS (
            SELECT
                MIN(CAST(order_purchase_timestamp AS DATE)) AS min_date,
                MAX(CAST(order_purchase_timestamp AS DATE)) AS max_date
            FROM raw_orders
        ),
        days AS (
            SELECT CAST(generate_series AS DATE) AS date
            FROM bounds, generate_series(bounds.min_date, bounds.max_date, INTERVAL 1 DAY)
        )
        SELECT
            date,
            YEAR(date) AS year,
            MONTH(date) AS month,
            STRFTIME(date, '%B') AS month_name,
            QUARTER(date) AS quarter
        FROM days
        ORDER BY date;
    """)

    # --- reviews deduped to one row per order_id ----------------------------
    con.execute("""
        CREATE OR REPLACE TABLE reviews_dedup AS
        SELECT order_id, review_score
        FROM (
            SELECT
                order_id,
                review_score,
                ROW_NUMBER() OVER (
                    PARTITION BY order_id
                    ORDER BY review_creation_date DESC
                ) AS rn
            FROM raw_reviews
        )
        WHERE rn = 1;
    """)

    # --- dim_orders ----------------------------------------------------------
    con.execute("""
        CREATE OR REPLACE TABLE dim_orders AS
        SELECT
            o.order_id,
            o.customer_id,
            o.order_status,
            o.order_purchase_timestamp AS purchase_ts,
            o.order_delivered_customer_date AS delivered_ts,
            o.order_estimated_delivery_date AS estimated_ts,
            DATE_DIFF('day', o.order_purchase_timestamp, o.order_delivered_customer_date) AS delivery_days,
            DATE_DIFF('day', o.order_purchase_timestamp, o.order_estimated_delivery_date) AS estimated_days,
            CASE
                WHEN o.order_delivered_customer_date IS NULL THEN NULL
                ELSE o.order_delivered_customer_date > o.order_estimated_delivery_date
            END AS is_late,
            r.review_score
        FROM raw_orders o
        LEFT JOIN reviews_dedup r ON o.order_id = r.order_id;
    """)

    # --- fct_order_items -------------------------------------------------
    con.execute("""
        CREATE OR REPLACE TABLE fct_order_items AS
        SELECT
            oi.order_id,
            oi.product_id,
            oi.seller_id,
            CAST(o.order_purchase_timestamp AS DATE) AS order_date,
            oi.price,
            oi.freight_value
        FROM raw_order_items oi
        INNER JOIN raw_orders o ON oi.order_id = o.order_id;
    """)


def sanity_checks(con: duckdb.DuckDBPyConnection) -> None:
    print("\n--- Sanity checks ---")

    order_items_rows = con.execute("SELECT COUNT(*) FROM raw_order_items").fetchone()[0]
    fact_rows = con.execute("SELECT COUNT(*) FROM fct_order_items").fetchone()[0]
    status = "OK" if order_items_rows == fact_rows else "MISMATCH"
    print(f"[{status}] fct_order_items rows = {fact_rows} vs raw order_items rows = {order_items_rows}")

    negative_delivery = con.execute(
        "SELECT COUNT(*) FROM dim_orders WHERE delivery_days < 0"
    ).fetchone()[0]
    status = "OK" if negative_delivery == 0 else "FAIL"
    print(f"[{status}] negative delivery_days rows = {negative_delivery}")

    dup_customers = con.execute(
        "SELECT COUNT(*) - COUNT(DISTINCT customer_id) FROM dim_customers"
    ).fetchone()[0]
    status = "OK" if dup_customers == 0 else "FAIL"
    print(f"[{status}] duplicate customer_id count = {dup_customers}")

    dup_orders = con.execute(
        "SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM dim_orders"
    ).fetchone()[0]
    status = "OK" if dup_orders == 0 else "FAIL"
    print(f"[{status}] duplicate order_id count = {dup_orders}")

    unknown_categories = con.execute(
        "SELECT COUNT(*) FROM dim_products WHERE product_category = 'unknown'"
    ).fetchone()[0]
    print(f"[INFO] products with unknown category = {unknown_categories}")


def write_outputs(con: duckdb.DuckDBPyConnection) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    tables = [
        "fct_order_items",
        "dim_orders",
        "dim_customers",
        "dim_products",
        "dim_sellers",
        "dim_date",
    ]

    print("\n--- Row counts ---")
    for table in tables:
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count} rows")

        csv_path = (PROCESSED / f"{table}.csv").as_posix()
        parquet_path = (PROCESSED / f"{table}.parquet").as_posix()
        con.execute(f"COPY {table} TO '{csv_path}' (FORMAT CSV, HEADER);")
        con.execute(f"COPY {table} TO '{parquet_path}' (FORMAT PARQUET);")


def main() -> None:
    con = duckdb.connect()
    build(con)
    sanity_checks(con)
    write_outputs(con)
    con.close()
    print(f"\nDone. Outputs written to {PROCESSED}")


if __name__ == "__main__":
    main()
