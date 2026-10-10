"""Load the Olist CSVs from data/raw into a SQLite database and print a quick profile.

Usage: python scripts/load_data.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "processed" / "olist.db"
SCHEMA = ROOT / "sql" / "01_schema.sql"

FILES = {
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
}

# Zip codes have leading zeros, so read them as text
TEXT_COLS = {
    "customer_zip_code_prefix": str,
    "seller_zip_code_prefix": str,
    "geolocation_zip_code_prefix": str,
}


def main() -> None:
    missing = [f for f in FILES.values() if not (RAW / f).exists()]
    if missing:
        raise SystemExit(
            "Missing files in data/raw:\n  " + "\n  ".join(missing)
            + "\nDownload the dataset from https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
        )

    DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as con:
        con.executescript(SCHEMA.read_text())
        print(f"{'table':<22}{'rows':>10}{'cols':>6}  nulls")
        for table, file in FILES.items():
            df = pd.read_csv(RAW / file, dtype=TEXT_COLS)
            df.to_sql(table, con, if_exists="append", index=False)
            nulls = df.isna().sum()
            nulls = ", ".join(f"{c}={n}" for c, n in nulls[nulls > 0].items()) or "-"
            print(f"{table:<22}{len(df):>10,}{df.shape[1]:>6}  {nulls}")
    print(f"\nDatabase written to {DB.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
