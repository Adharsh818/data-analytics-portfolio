# Power BI dashboard: build guide

A 3-page dashboard on the Olist star schema. Building it yourself takes about 1-2 hours and
is worth it: interviewers often ask you to walk through how you modelled the data and wrote the DAX.

## 1. Generate the data

```bash
python scripts/load_data.py        # raw CSVs -> SQLite
python scripts/build_notebook.py   # cleaning + analysis, exports clean tables
python scripts/export_powerbi.py   # star schema -> data/processed/powerbi/
```

## 2. Load the tables

Power BI Desktop > **Get data > Text/CSV**, and load all five files from `data/processed/powerbi/`:

| Table | Grain | Key |
|---|---|---|
| `fact_orders` | one row per order (all statuses) | `order_id` |
| `fact_order_items` | one row per item | `order_id` + `order_item_id` |
| `dim_customer` | one row per customer, with RFM segment | `customer_unique_id` |
| `dim_state` | 27 Brazilian states with region | `state_code` |
| `dim_date` | one row per day, Jan 2017 - Aug 2018 | `date` |

In Power Query, check these types: `purchase_date` and `date` = Date; `revenue`, `price`,
`freight` = Decimal; `is_late`, `is_delivered` = Whole number.

## 3. Model (Model view)

Create these relationships (all many-to-one, single direction):

```
fact_orders[purchase_date]      -> dim_date[date]
fact_orders[customer_unique_id] -> dim_customer[customer_unique_id]
fact_orders[customer_state]     -> dim_state[state_code]
fact_order_items[order_id]      -> fact_orders[order_id]
```

Then:
- Mark `dim_date` as a date table (Table tools > Mark as date table > `date`).
- Sort `dim_date[month]` by `month_num` and `dim_date[weekday]` by `weekday_num`.
- Set `dim_state[state_name]` data category to **State or Province** and `country` to **Country** (for the map).
- Delete the auto-detected relationship from `fact_order_items[purchase_date]` if Power BI creates one.

## 4. Measures

Create a `_Measures` table (Home > Enter data > OK) and add every measure from
[`measures.dax`](measures.dax). Format: revenue as currency R$ with 0 decimals, % measures as percentage.

## 5. Pages

Use one consistent look: white background, navy titles (#1F3A5F), one accent blue (#2563EB),
red (#DC2626) only for "bad" things like late deliveries. Put slicers for **Year**, **Region**
and **Payment type** on every page and sync them (View > Sync slicers).

### Page 1: Sales Overview
| Visual | Fields |
|---|---|
| 4 cards | Total Revenue, Delivered Orders, Avg Order Value, Customers |
| Line chart | X: `dim_date[year_month]`, Y: Total Revenue |
| Bar chart (top 10) | Y: `fact_order_items[category]`, X: Category Revenue (Filters pane > Top N = 10) |
| Filled map | Location: `dim_state[state_name]`, color saturation: Total Revenue |
| Column chart | X: `dim_date[weekday]`, Y: Delivered Orders |

Title idea: "Revenue grew ~8x in 2017 and plateaued in 2018".

### Page 2: Delivery & Satisfaction
| Visual | Fields |
|---|---|
| 3 cards | Late Delivery %, Avg Delivery Days, Avg Review |
| Column chart | X: `fact_orders[delivery_bucket]`, Y: Avg Review (data labels on) |
| Bar chart | Y: `dim_state[state_code]`, X: Late Delivery % (sort descending) |
| Line + column chart | X: `dim_date[year_month]`, columns: Delivered Orders, line: Late Delivery % |

Title idea: "Late orders lose up to 2.6 stars".

### Page 3: Customers
| Visual | Fields |
|---|---|
| 2 cards | Repeat Customer %, Customers |
| Donut | Legend: `dim_customer[segment]`, Values: Segment Customers |
| Bar chart | Y: `dim_customer[segment]`, X: Segment Revenue Share |
| Table | `dim_customer[segment]`, Segment Customers, Total Revenue, Avg Order Value |

Title idea: "97% of customers buy only once".

## 6. Check your numbers

With no slicers applied, your cards should show:

| Measure | Expected |
|---|---|
| Total Revenue | R$ 13,179,778 |
| Delivered Orders | 96,203 |
| Avg Order Value | R$ 137.00 |
| Customers | 93,096 |
| Avg Review | 4.16 |
| Late Delivery % | 6.8% |
| Repeat Customer % | 3.0% |

If they match, the model is right.

## 7. Save and publish

- Save as `powerbi/olist_dashboard.pbix`.
- Export each page as an image (File > Export > PDF, or screenshot) into `powerbi/screenshots/`
  so the README can show it to recruiters who don't have Power BI.
- Optional: publish to the Power BI service and add the public link to the README.
