# Report Layout

Three pages, each answering a subset of the business questions in
`plan.md` §4. Build in Power BI Desktop after Phase 4 (all `_Measures` are
in place). General conventions for every page are at the bottom — read
those before building the first page.

---

## Page 1 — Executive overview

Answers: revenue/volume trend (Q1), top categories and states by revenue
(Q4).

**KPI cards** (top row, four cards left to right):
- `[Total Revenue]`
- `[Total Orders]`
- `[Avg Delivery Days]`
- `[Late Delivery Rate]`

**Revenue trend line by month** (line chart, full width below cards):
- Axis: `dim_date[date]` — use the built-in date hierarchy, then
  double-click to drill down to the **Month** level so the axis shows
  every calendar month across the full 2016–2018 range (not just 12
  buckets). Turn off "Concatenate labels" if the axis switches to
  hierarchy-drill mode so you get a continuous Year→Month line.
- Values: `[Total Revenue]`
- Optional: add `[Revenue MoM %]` as a line on a secondary axis to show
  growth rate alongside the absolute trend.

**Revenue by state** (filled map, bottom left):
- Location: `dim_customers[customer_state]`. Brazilian 2-letter state
  codes (SP, RJ, MG, ...) can geocode ambiguously on Bing Maps without
  country context. If pins land wrong or don't resolve, add a computed
  column `State (map) = dim_customers[customer_state] & ", Brazil"` and
  use that as Location instead.
- Values: `[Total Revenue]`

**Top 10 categories** (horizontal bar chart, bottom right):
- Axis: `dim_products[product_category]`
- Values: `[Total Revenue]`
- Visual-level filter: **Top N** → Top 10 by `[Total Revenue]`

**Slicer:** `dim_date[year]`, placed top-right, applies to this page only.

---

## Page 2 — Delivery performance

Answers: actual vs. estimated delivery time and late-delivery share (Q2).

**Avg Delivery vs Avg Estimated** (clustered column chart, top left):
- Axis: `dim_date[year]`
- Values: `[Avg Delivery Days]`, `[Avg Estimated Days]` (clustered)

**Late Delivery Rate by state** (bar chart, top right):
- Axis: `dim_customers[customer_state]` — customer state, since lateness
  is experienced at the delivery end, not the seller end.
- Values: `[Late Delivery Rate]`
- Sort descending so the worst-performing states are immediately visible.

**Distribution of delivery_days** (column chart, bottom left):
- `dim_orders[delivery_days]` doesn't have a measure to plot directly as a
  histogram — Power BI has no native histogram visual. Right-click
  `dim_orders[delivery_days]` in the field list → **New group** → bin size
  5 (days) to create a `delivery_days (bins)` column.
- Axis: `delivery_days (bins)`
- Values: **Count of** `dim_orders[order_id]` (drag the column into
  Values, it defaults to Count — don't use `[Total Orders]` here, since
  that measure undercounts by construction; see the gotcha in
  `dax_measures.md`).

**Drill-through to order detail** (bottom right, or triggered from any
visual on this page):
1. Add a new page named **Order Detail**.
2. Drag `dim_customers[customer_state]` into the **Drillthrough** filter
   well.
3. Add a Table visual with: `dim_orders[order_id]`, `purchase_ts`,
   `delivered_ts`, `estimated_ts`, `delivery_days`, `estimated_days`,
   `is_late`, `review_score`, `dim_products[product_category]`,
   `fct_order_items[price]`, `fct_order_items[freight_value]`.
4. Power BI auto-adds a **Back** button — keep it.
5. Right-click **Order Detail** in the page tab → **Hide page** (it's
   reached only via drillthrough, not direct navigation).
6. Test: on Page 2, right-click a bar in "Late Delivery Rate by state" →
   **Drillthrough → Order Detail**.

---

## Page 3 — Freight & reviews

Answers: freight as a share of revenue (Q3), late delivery vs. review
score correlation (Q5).

**Freight % of Revenue by category** (bar chart, top left):
- Axis: `dim_products[product_category]`
- Values: `[Freight % of Revenue]`
- Sort descending.

**Freight % of Revenue by state** (bar chart, top right):
- Axis: `dim_sellers[seller_state]` — seller state, not customer state.
  Freight is driven by the seller→customer shipping distance, so
  decomposing by seller origin isolates the supply-chain cost driver
  rather than mixing it with delivery-destination effects already covered
  on Page 2.
- Values: `[Freight % of Revenue]`

**Scatter: Avg Delivery Days vs Avg Review Score** (bottom, full width):
- X axis: `[Avg Delivery Days]`
- Y axis: `[Avg Review Score]`
- Details: `dim_products[product_category]` — one dot per category (~33
  categories) gives enough points to see a correlation pattern. If the
  category view looks too noisy, swap Details to
  `dim_customers[customer_state]` instead (~27 states) — don't use both at
  once.
- Size (optional): `[Total Orders]`, so larger categories/states are
  visually weighted.

---

## Conventions (apply to all three pages)

- **Number formats** — set once on each measure (Modeling tab → select
  measure → Format):
  - `Total Revenue`, `Total Freight`: Currency, custom format
    `"R$"\ #,##0.00` (Power BI's built-in `$` symbol is wrong for BRL).
  - `Freight % of Revenue`, `Late Delivery Rate`, `Revenue MoM %`:
    Percentage, 1 decimal place.
  - `Avg Delivery Days`, `Avg Estimated Days`: Decimal Number, 1 decimal
    place, suffix " days" via a custom format if desired.
  - `Avg Review Score`: Decimal Number, 2 decimal places.
- **Theme** — Format (ribbon) → Themes → pick one built-in theme and apply
  it to all three pages before final formatting passes, so colors are
  consistent report-wide. Don't mix default and custom-themed visuals.
- **Titles** — sentence case (e.g. "Revenue by state", not "Revenue By
  State" or "REVENUE BY STATE"). Every visual gets an explicit title; turn
  off auto-generated titles that just repeat the field name.
- **Page titles** — a text box at the top of each page: "Executive
  overview", "Delivery performance", "Freight & reviews".
