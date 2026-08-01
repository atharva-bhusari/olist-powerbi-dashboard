# Power BI Modeling Steps

Exact click-path for loading the star schema into Power BI Desktop and wiring
up relationships. Source tables are the six files in `data/processed/`,
produced by `src/prep_data.py` (see [`data_dictionary.md`](data_dictionary.md)
for columns). Do this after Phase 2 (`data/processed/` is populated).

## 1. Load the six tables

Repeat for each of the six CSVs:

1. **Home → Get Data → Text/CSV**.
2. Browse to `data/processed/<table>.csv`.
3. In the preview window, confirm the delimiter is comma and "File Origin" is
   `65001: Unicode (UTF-8)`.
4. Click **Load** (not "Transform Data" — the pipeline already typed and
   cleaned the columns, so no Power Query editing is needed).

Load, in order:

- `fct_order_items.csv`
- `dim_orders.csv`
- `dim_customers.csv`
- `dim_products.csv`
- `dim_sellers.csv`
- `dim_date.csv`

**Check data types after load** (Table view, click each column header): Power
BI's auto-detection usually gets these right, but confirm:
- `fct_order_items[order_date]` and `dim_date[date]` → **Date**
- `dim_orders[purchase_ts]`, `[delivered_ts]`, `[estimated_ts]` → **Date/Time**
- `fct_order_items[price]`, `[freight_value]` → **Decimal Number** or **Fixed
  Decimal Number** (fixed decimal avoids floating-point rounding on currency)
- `dim_orders[is_late]` → **True/False**

## 2. Build relationships

Switch to **Model view** (left nav, the icon with three connected boxes).
Drag from the FK column on `fct_order_items` / `dim_orders` to the PK column
on the target dimension to create each relationship, or use **Manage
Relationships → New**. For every relationship below: cardinality
**Many-to-one (*:1)**, cross-filter direction **Single**, pointing from the
fact/child side toward the dimension.

| From | To | Cardinality | Cross-filter |
|---|---|---|---|
| `fct_order_items[order_id]` | `dim_orders[order_id]` | Many-to-one | Single |
| `fct_order_items[product_id]` | `dim_products[product_id]` | Many-to-one | Single |
| `fct_order_items[seller_id]` | `dim_sellers[seller_id]` | Many-to-one | Single |
| `fct_order_items[order_date]` | `dim_date[date]` | Many-to-one | Single |
| `dim_orders[customer_id]` | `dim_customers[customer_id]` | Many-to-one | Single |

This gives a standard star: `fct_order_items` at the center, four dimensions
one hop away, and `dim_customers` two hops away through `dim_orders`. Do not
set any relationship to bidirectional — single-direction many-to-one keeps
filter propagation predictable and avoids ambiguity errors.

## 3. Mark dim_date as the official date table

1. In **Model view** (or Table view), click the `dim_date` table.
2. **Table tools → Mark as Date Table → Mark as Date Table**.
3. In the dialog, set the date column to `date`. Click **OK**.

This enables time-intelligence DAX (`DATEADD`, `SAMEPERIODLASTYEAR`, etc.) in
Phase 4 and ensures Power BI validates `dim_date` has one row per day with no
gaps or duplicates over the full range.

## 4. Hide FK columns from report view

In **Model view**, for each column below: right-click → **Hide in Report
View** (or select the column and toggle the eye icon in the Properties
pane).

- `fct_order_items`: `order_id`, `product_id`, `seller_id`
- `dim_orders`: `customer_id`

Keep PK columns on the dimension tables (`dim_orders[order_id]`,
`dim_customers[customer_id]`, etc.) visible — they're still useful for
troubleshooting and drill-through, and hiding them isn't required for a
clean field list since users browse dimensions by their descriptive columns.

## Verification checklist

- [ ] All six tables loaded, correct row counts match
      [`data_dictionary.md`](data_dictionary.md).
- [ ] Five relationships exist, all many-to-one / single-direction, no
      dashed (inactive) lines and no cross-filter warnings.
- [ ] `dim_date` shows a calendar icon in the field list (confirms it's
      marked as the date table).
- [ ] Field list no longer shows raw ID columns under `fct_order_items` or
      `dim_orders[customer_id]`.
- [ ] A quick test visual — e.g. a table of `dim_date[year]` x
      `SUM(fct_order_items[price])` — returns non-blank values for every
      year in the data, confirming the fact-to-date relationship works.
