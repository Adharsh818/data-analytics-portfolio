"""Create the cleaned views and run every named query in sql/03-08.

Each query starts with a `-- name: <query_name>` comment. Results are printed and saved
to data/processed/sql_results/<file>__<query_name>.csv.

Usage: python scripts/run_sql.py
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "processed" / "olist.db"
OUT = ROOT / "data" / "processed" / "sql_results"
SKIP = {"01_schema.sql", "02_clean_views.sql"}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)
    with sqlite3.connect(DB) as con:
        con.executescript((ROOT / "sql" / "02_clean_views.sql").read_text(encoding="utf-8"))
        for path in sorted((ROOT / "sql").glob("0*.sql")):
            if path.name in SKIP:
                continue
            text = path.read_text(encoding="utf-8")
            for name, query in re.findall(r"-- name: (\w+)\n(.*?)(?=\n-- name:|\Z)", text, re.S):
                df = pd.read_sql_query(query, con)
                df.to_csv(OUT / f"{path.stem}__{name}.csv", index=False)
                print(f"\n=== {path.stem} / {name} ===\n{df.to_string(index=False)}")


if __name__ == "__main__":
    main()
