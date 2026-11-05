# Open and check the Power BI project

The repository includes `olist_dashboard.pbip`, an `Olist.Report` folder and an
`Olist.SemanticModel` folder. These are editable Power BI project files, not a PBIX.
The report has Sales, Delivery and Customers pages, 30 visuals and 15 measures.

## Open and refresh

1. Run the Python pipeline in the main README. If the generated CSVs already exist,
   run `python scripts/build_powerbi_project.py` from the repository root. This sets
   the local `DataFolder` parameter to the correct absolute path.
2. Open `powerbi/olist_dashboard.pbip` in a current Power BI Desktop version supporting
   PBIP and PBIR. Project support may require enabling the relevant preview feature.
3. Refresh. If you moved the repository, use Transform data → Manage parameters to
   set `DataFolder` to the full path of `data/processed/powerbi`, then apply and refresh.
4. In Model view, confirm `dim_date` is marked as a date table with `date` as its key.
5. Check the totals and filter tests below. Save a local PBIX if desired.

No account sign-in or online publishing is necessary to review locally.

## Model

```text
dim_date[date] -------------------< fact_orders[purchase_date]
dim_state[state_code] -----------< fact_orders[customer_state]
dim_customer[customer_unique_id]-< fact_orders[customer_unique_id]
fact_orders[order_id] -----------< fact_order_items[order_id]
```

Relationships filter from the unique side to the many side. There is no direct date
relationship to items: date filters reach items through orders. This prevents an
ambiguous second filter path. It is an order/item model, with dimensions on orders.

The fact tables contain all statuses **among orders that have items**. `is_delivered=1`
means delivered with a known delivery timestamp, matching SQL, Python and Excel.
Do not calculate overall cancellation rate from this model: itemless orders were excluded.
Category Revenue sums item prices; Total Revenue sums order totals.

## Report pages

| Page | Content |
|---|---|
| Sales | Revenue, delivered orders, AOV, customers; monthly sales; category and state sales. |
| Delivery | Late rate, delivery duration, reviews, bad-review share; lateness buckets, state rates and monthly trend. |
| Customers | Customers, repeat share, revenue, AOV; full-window RFM segments and monthly purchasing customers. |

Each page has synced purchase-year, state and largest-payment-type slicers.
RFM segment labels remain fixed at the full-window snapshot. Repeat Customer % is
recomputed within the selected context; it is not a fixed historical churn metric.

Selecting an item category does not propagate backwards to order KPIs with these
single-direction relationships. Use the year/state/payment slicers for whole-report
filtering. Category sales reconcile with order sales with no category selection.
State late-rate charts include small states; compare eligible order volume before
prioritising a state. SQL's state ranking intentionally requires at least 500 orders.

## Check before sharing

Clear slicers and selections. Expected totals:

| Measure | Expected |
|---|---|
| Total Revenue | R$13,179,777.95 (R$13,179,778 rounded) |
| Delivered Orders | 96,203 |
| Avg Order Value | R$137.00 |
| Customers | 93,096 |
| Avg Review | 4.16 |
| Late Delivery % | 6.8% |
| Repeat Customer % | 3.0% |

Then check:

- January 2017: 750 delivered orders and revenue R$111,798 rounded.
- State SP: compare revenue and late rate against the SQL state outputs.
- State + year + payment: cards and charts should respond together on all pages.
- Segment customer counts should sum to Customers under the same slicers.
- Bad Review % excludes blank review scores from both numerator and denominator.
- Delivery buckets are ordered on-time, 1–3, 4–7, 8+ days late.
- Clear all selections and confirm the baseline returns.
- Inspect all pages for clipping and working visuals, then save and reopen.

Export authentic Desktop page screenshots into `powerbi/screenshots/` after passing
these checks. The notebook charts are available for immediate viewing, but are not
Power BI screenshots.

## Validation status and format references

All 39 report/project JSON definitions passed `python scripts/validate_powerbi.py`.
The data exports reconcile to SQL/pandas. **Power Query refresh, DAX evaluation,
visual rendering and interactions have not been verified in Desktop** because the
desktop automation helper failed to initialize. Complete the checks above before
claiming a fully tested Power BI dashboard.

The public schemas validate the file structure, not visual role semantics or DAX results.
`model.bim` is a semantic model definition and is not included in PBIR schema validation.

- [Microsoft PBIP overview](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview)
- [Report folder and PBIR format](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report)
- [Microsoft JSON schemas](https://github.com/microsoft/json-schemas/tree/main/fabric)
