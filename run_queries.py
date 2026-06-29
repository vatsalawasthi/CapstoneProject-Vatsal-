"""
run_queries.py
---------------
Day 2 Task: run the 10 analytical SQL queries in sql/queries.sql against
bluestock_mf.db and print the results (also useful as a quick sanity check
that the database loaded correctly).

Run:
    python run_queries.py
"""

import re

import pandas as pd
from sqlalchemy import create_engine

from common import SQL_DIR, DB_PATH, log_section

QUERY_LABELS = [
    "Q1. Top 5 funds by AUM",
    "Q2. Average NAV per month",
    "Q3. SIP YoY growth",
    "Q4. Transactions by state",
    "Q5. Funds with expense_ratio < 1%",
    "Q6. Top 5 funds by 3-year return",
    "Q7. SIP vs Lumpsum vs Redemption breakdown",
    "Q8. Sector exposure across portfolio holdings",
    "Q9. Monthly net category inflows: Large Cap vs Small Cap",
    "Q10. KYC-pending transactions by payment mode",
]


def split_statements(sql_text: str):
    """Strip '--' comment lines, then split on ';' into individual statements."""
    lines = [l for l in sql_text.splitlines() if not l.strip().startswith("--")]
    cleaned = "\n".join(lines)
    return [s.strip() for s in cleaned.split(";") if s.strip()]


def main():
    log_section("RUNNING: 10 analytical queries from sql/queries.sql")

    engine = create_engine(f"sqlite:///{DB_PATH}")
    sql_text = (SQL_DIR / "queries.sql").read_text(encoding="utf-8")
    statements = split_statements(sql_text)

    if len(statements) != len(QUERY_LABELS):
        print(f"  NOTE: found {len(statements)} SQL statements but expected "
              f"{len(QUERY_LABELS)} -- labels may not line up 1:1, check sql/queries.sql.")

    with engine.connect() as conn:
        for i, stmt in enumerate(statements):
            label = QUERY_LABELS[i] if i < len(QUERY_LABELS) else f"Query {i + 1}"
            print(f"\n{'-' * 70}\n{label}\n{'-' * 70}")
            df = pd.read_sql(stmt, conn)
            print(df.to_string(index=False))


if __name__ == "__main__":
    main()