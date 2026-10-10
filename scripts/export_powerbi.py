"""Export a star schema for Power BI to data/processed/powerbi/.

Tables:
  fact_orders       one row per order (all statuses) in the analysis window
  fact_order_items  one row per item, with category and seller
  dim_customer      one row per customer_unique_id with RFM segment
  dim_state         Brazilian state code, name and region
  dim_date          calendar table covering the window

Usage: python scripts/export_powerbi.py   (run scripts/build_notebook.py first)
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
OUT = PROC / "powerbi"

STATES = {
    "AC": ("Acre", "North"), "AL": ("Alagoas", "Northeast"), "AP": ("Amapá", "North"),
    "AM": ("Amazonas", "North"), "BA": ("Bahia", "Northeast"), "CE": ("Ceará", "Northeast"),
    "DF": ("Distrito Federal", "Central-West"), "ES": ("Espírito Santo", "Southeast"),
    "GO": ("Goiás", "Central-West"), "MA": ("Maranhão", "Northeast"), "MT": ("Mato Grosso", "Central-West"),
    "MS": ("Mato Grosso do Sul", "Central-West"), "MG": ("Minas Gerais", "Southeast"), "PA": ("Pará", "North"),
    "PB": ("Paraíba", "Northeast"), "PR": ("Paraná", "South"), "PE": ("Pernambuco", "Northeast"),
    "PI": ("Piauí", "Northeast"), "RJ": ("Rio de Janeiro", "Southeast"), "RN": ("Rio Grande do Norte", "Northeast"),
    "RS": ("Rio Grande do Sul", "South"), "RO": ("Rondônia", "North"), "RR": ("Roraima", "North"),
    "SC": ("Santa Catarina", "South"), "SP": ("São Paulo", "Southeast"), "SE": ("Sergipe", "Northeast"),
    "TO": ("Tocantins", "North"),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    orders = pd.read_csv(PROC / "orders_clean.csv", parse_dates=["purchase_date"])
    items = pd.read_csv(PROC / "order_items_clean.csv", parse_dates=["purchase_date"])
    rfm = pd.read_csv(PROC / "customers_rfm.csv")

    orders["delivery_bucket"] = pd.cut(orders["days_vs_estimate"], [-np.inf, 0, 3, 7, np.inf],
                                       labels=["On time / early", "1-3 days late", "4-7 days late", "8+ days late"])
    orders["is_delivered"] = (orders["order_status"] == "delivered").astype(int)
    fact_orders = orders.drop(columns=["customer_city", "purchase_month"])
    fact_orders.to_csv(OUT / "fact_orders.csv", index=False)

    items.drop(columns=["order_status"]).to_csv(OUT / "fact_order_items.csv", index=False)

    cust = (orders.sort_values("purchase_date")
            .groupby("customer_unique_id")[["customer_city", "customer_state"]].last()
            .join(rfm.set_index("customer_unique_id")[["recency_days", "frequency", "monetary", "R", "F", "M", "segment"]])
            .reset_index())
    cust["segment"] = cust["segment"].fillna("No delivered order")
    cust.to_csv(OUT / "dim_customer.csv", index=False)

    pd.DataFrame([(k, n, r) for k, (n, r) in STATES.items()],
                 columns=["state_code", "state_name", "region"]).assign(
        country="Brazil").to_csv(OUT / "dim_state.csv", index=False, encoding="utf-8-sig")

    d = pd.DataFrame({"date": pd.date_range("2017-01-01", "2018-08-31")})
    d["year"] = d["date"].dt.year
    d["quarter"] = "Q" + d["date"].dt.quarter.astype(str)
    d["month_num"] = d["date"].dt.month
    d["month"] = d["date"].dt.strftime("%b")
    d["year_month"] = d["date"].dt.strftime("%Y-%m")
    d["weekday_num"] = d["date"].dt.dayofweek + 1
    d["weekday"] = d["date"].dt.strftime("%a")
    d.to_csv(OUT / "dim_date.csv", index=False)

    for p in sorted(OUT.glob("*.csv")):
        print(f"{p.name:<22}{sum(1 for _ in open(p, encoding='utf-8-sig')) - 1:>9,} rows")


if __name__ == "__main__":
    main()
