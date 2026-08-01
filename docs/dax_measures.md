# DAX Measures

All measures below live in a dedicated `_Measures` table (not tied to any
data table) so they're easy to find in the field list, separate from data
columns.

## Create the `_Measures` table

1. **Modeling → New Table**.
2. Enter: `_Measures = {BLANK()}`
3. In the table's one column (`Value`), right-click → **Hide in Report
   View** — it's a placeholder, not something to visualize.
4. Select the `_Measures` table, then **Modeling → New Measure** for each
   measure below. (New measures created while `_Measures` is selected in
   the field list get placed inside it automatically.)

## Measures

### Total Revenue
```dax
Total Revenue = SUM(fct_order_items[price])
```
Sum of item-line prices, excluding freight. This is the core revenue figure
everything else (freight %, MoM growth) is measured against.

### Total Freight
```dax
Total Freight = SUM(fct_order_items[freight_value])
```
Sum of freight charged across all order line items — the raw cost side of
the delivery/supply-chain story.

### Freight % of Revenue
```dax
Freight % of Revenue = DIVIDE([Total Freight], [Total Revenue])
```
Freight as a share of revenue. Uses `DIVIDE` instead of `/` so a filter
context with zero revenue (e.g. an empty slicer selection) returns blank
instead of erroring.

### Total Orders
```dax
Total Orders = DISTINCTCOUNT(fct_order_items[order_id])
```
Distinct order count from the fact table (not `COUNTROWS`, since one order
can span multiple line items — counting rows would overcount orders with
several products).

### Avg Delivery Days
```dax
Avg Delivery Days = AVERAGE(dim_orders[delivery_days])
```
Average actual delivery time in days. `delivery_days` is blank for orders
not yet delivered, and `AVERAGE` skips blanks automatically, so this only
reflects orders that actually arrived.

### Avg Estimated Days
```dax
Avg Estimated Days = AVERAGE(dim_orders[estimated_days])
```
Average promised delivery time in days, for comparison against actual
delivery time in a clustered bar chart (Phase 5, page 2).

### Late Delivery Rate
```dax
Late Delivery Rate =
DIVIDE(
    CALCULATE(COUNTROWS(dim_orders), dim_orders[is_late] = TRUE()),
    COUNTROWS(dim_orders)
)
```
Share of orders delivered after their estimated date. Note the denominator
is **all orders in context**, including ones never delivered (`is_late` is
blank for those, so they fall out of the numerator but stay in the
denominator) — this measure answers "of everything ordered, what fraction
arrived late," not "of everything delivered, what fraction was late." Call
this out explicitly if it comes up in an interview.

### Avg Review Score
```dax
Avg Review Score = AVERAGE(dim_orders[review_score])
```
Average customer review score (1–5). Blank for orders with no review;
`AVERAGE` ignores those rather than treating them as zero.

### Revenue MoM %
```dax
Revenue MoM % =
VAR CurrentRevenue = [Total Revenue]
VAR PriorRevenue =
    CALCULATE([Total Revenue], DATEADD(dim_date[date], -1, MONTH))
RETURN
    DIVIDE(CurrentRevenue - PriorRevenue, PriorRevenue)
```
Month-over-month revenue growth. `DATEADD` requires `dim_date` to be marked
as the model's official date table with a contiguous daily range (done in
Phase 3) — otherwise it silently returns wrong shifted periods.

## Validation

Ground-truth values computed directly from `data/processed/` via DuckDB,
independent of the Power BI model. Clear all slicers/filters before
comparing — these are grand-total figures.

| Measure | Expected value |
|---|---|
| Total Revenue | 13,591,643.70 |
| Total Freight | 2,251,909.54 |
| Freight % of Revenue | 16.57% |
| Total Orders | **98,666** |
| Avg Delivery Days | 12.5 |
| Avg Estimated Days | 24.4 |
| Late Delivery Rate | 7.87% |
| Avg Review Score | 4.086 |

**Total Orders gotcha:** this reads 98,666, not the 99,441 rows in
`dim_orders`. 775 orders in `dim_orders` have zero rows in
`fct_order_items` (canceled/unavailable orders that never got a line item),
so `DISTINCTCOUNT(fct_order_items[order_id])` can't see them. A card built
off `dim_orders` row count instead would correctly show 99,441 — the two
are supposed to disagree.

**Revenue MoM % spot checks** — filter to a single month and compare:
- **Feb 2018** → expect **−11.14%** (Jan 2018 revenue 950,030.36 → Feb
  844,178.71)
- **Apr 2018** → expect **+1.37%** (Mar 2018 revenue 983,213.44 → Apr
  996,647.75)

**General validation approach:**
1. Clear all slicers/filters before comparing to the table above.
2. For ratio measures (Freight %, Late Rate), verify by manually dividing
   the two underlying Card values — a mismatch there points to `DIVIDE`
   usage, not the source data.
3. Drop `dim_date[year]` on rows next to a measure in a Table visual and
   compare a couple of years against a quick DuckDB `GROUP BY year` — this
   catches relationship/filter-propagation bugs that grand totals hide.
