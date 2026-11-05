# Project walkthrough and interview preparation

Use the wording below after reviewing the queries, notebook and reports. Describe help
received accurately if asked; claim only work and reasoning you can explain.

## A 60-second walkthrough

“I used public Olist marketplace data to practise retail analytics with SQL, Python,
Excel and Power BI. I wanted to understand sales performance and where customer
experience needed investigation. I aggregated items, payments and reviews to the right
grain before joining, defined delivered merchandise sales consistently, and checked SQL
against pandas. The analysis covers about 96,000 delivered orders and R$13.18 million
in item sales. Orders delivered eight or more days late had much lower review scores
than on-time orders. I would investigate delivery promises and regional fulfilment,
then test changes. The study shows associations, not proven business impact.”

## Questions to prepare

1. **Why Olist for a retail role in Bengaluru?** It has linked transactions, products,
   customers, sellers, delivery and reviews. It supports realistic joins and operational
   questions. Its historical Brazilian rates are not benchmarks for Indian or US stores.
2. **What join mistake matters most?** Two items and two payments can create four rows.
   Aggregate to order grain first; sum item prices before joining review/payment summaries.
3. **Why exclude freight from revenue?** It separates merchandise demand from shipping charges.
   It is still not profit or marketplace commission revenue.
4. **Why two customer IDs?** One is tied to an order record; the unique customer ID
   supports repeat-purchase analysis across orders.
5. **Does late delivery cause lower reviews?** The groups differ strongly, but this study
   does not isolate causality. Compare like-for-like sellers/categories/regions and test
   operational changes before estimating impact.
6. **Why blank recent cohort cells?** Those customers lack enough follow-up. A true zero
   means a month was observed and nobody returned.
7. **Are one-time customers churned?** Purchases outside the window/on other channels
   are unknown. A one-time durable-goods purchase can be normal.
8. **How do you verify a dashboard?** Reconcile counts, customers and revenue, then test
   a month, a state, missing reviews and filters. Matching one headline is insufficient.
9. **What would you add for stores?** Inventory turns need inventory snapshots and COGS;
   margin needs costs; promotion lift needs exposure and a comparison group.
10. **What remains unverified?** See review notes. Explain the difference between
    structurally validated files and a report refreshed/tested in Power BI Desktop.

## Demo order

Show the business summary, sales SQL, item/payment aggregation, delivery chart and a
reconciliation check. In Excel, change the state selector: it changes KPI cards only.
In Power BI, show relationships and change the state/year/payment slicers after the
Desktop checks pass.

## Resume bullets

Use the first two if you can demonstrate the work. Use the Power BI bullet after the
Desktop refresh and interaction checks pass.

- Analysed 96,203 delivered e-commerce orders using SQL and pandas, reconciling R$13.18M
  in merchandise sales and examining delivery reliability, customer cohorts and seller performance.
- Built a formula-driven Excel summary and visualised regional delivery issues; found
  average review scores of 4.29 for on-time orders versus 1.70 for orders 8+ days late.
- Built a three-page Power BI report with an order/item model, DAX measures and state,
  purchase-year and payment filters to explore retail sales and customer experience.

Do not claim revenue growth, cost savings, a deployed business solution or work for
the companies you are applying to. This project did not implement an intervention.

## Employer context checked on 5 November 2026

Target's internship overview describes sales/operations analysis and recommendations.
Walmart's Data & Tech Transformation internship mentions business questions, operational
priorities, SQL, Python and Power BI. These are examples of relevant skills, not proof
of an open Bengaluru vacancy or identical requirements for every role.

- [Target internship overview](https://corporate.target.com/careers/career-areas/intern-entry-level/internships)
- [Walmart Data & Tech Transformation internship](https://walmart.wd504.myworkdayjobs.com/WalmartExternal/job/USA-Always-AR-Bentonville-Home-Office/XMLNAME--USA--Summer-2027-Corporate-Intern---Data---Tech-Transformation-intern_R-2690457-1)
