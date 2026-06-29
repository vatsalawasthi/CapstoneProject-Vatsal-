"""
load_to_sqlite.py
-------------------
Day 2 Task: Load all cleaned datasets into SQLite.

What this script does:
  1. Generates dim_date (one row per calendar day, 2022-01-01 -> 2026-05-31).
  2. Executes sql/schema.sql against bluestock_mf.db (drops + recreates all
     tables -- safe to re-run).
  3. Loads dim_fund from data/processed/01_fund_master.csv.
  4. Loads every fact / supporting table from its matching cleaned CSV using
     SQLAlchemy's create_engine() + DataFrame.to_sql().
  5. Verifies row counts in SQLite match the source cleaned CSVs.

Run:
    python load_to_sqlite.py
"""

import sqlite3

import pandas as pd
from sqlalchemy import create_engine, text

from common import PROCESSED, SQL_DIR, DB_PATH, log_section

DATE_RANGE_START = "2022-01-01"
DATE_RANGE_END = "2026-05-31"


def build_dim_date() -> pd.DataFrame:
    dates = pd.date_range(DATE_RANGE_START, DATE_RANGE_END, freq="D")
    df = pd.DataFrame({"date_key": dates.strftime("%Y-%m-%d")})
    df["year"] = dates.year
    df["quarter"] = dates.quarter
    df["month"] = dates.month
    df["month_name"] = dates.strftime("%B")
    df["day"] = dates.day
    df["day_of_week"] = dates.dayofweek
    df["day_name"] = dates.strftime("%A")
    df["is_weekend"] = (dates.dayofweek >= 5).astype(int)
    df["year_month"] = dates.strftime("%Y-%m")
    return df


def apply_schema(conn: sqlite3.Connection):
    schema_sql = (SQL_DIR / "schema.sql").read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.commit()


def main():
    log_section("LOAD: building bluestock_mf.db")

    # ---- 1. Fresh sqlite3 connection to run the DDL script -----------------
    # (SQLAlchemy's engine is used for the bulk df.to_sql() loads below, but
    #  executescript() is simplest directly via sqlite3 for multi-statement DDL.)
    raw_conn = sqlite3.connect(DB_PATH)
    print(f"Applying schema.sql to {DB_PATH} ...")
    apply_schema(raw_conn)
    raw_conn.close()
    print("  Schema applied (all tables dropped + recreated).")

    engine = create_engine(f"sqlite:///{DB_PATH}")

    # ---- 2. dim_date ----------------------------------------------------------
    dim_date = build_dim_date()
    dim_date.to_sql("dim_date", engine, if_exists="append", index=False)
    print(f"  Loaded dim_date: {len(dim_date)} rows "
          f"({DATE_RANGE_START} -> {DATE_RANGE_END}).")

    # ---- 3. dim_fund ------------------------------------------------------------
    fund_master = pd.read_csv(PROCESSED["fund_master"])
    fund_master.to_sql("dim_fund", engine, if_exists="append", index=False)
    print(f"  Loaded dim_fund: {len(fund_master)} rows.")

    # ---- 4. fact_nav --------------------------------------------------------------
    nav = pd.read_csv(PROCESSED["nav_history"])
    nav["is_filled"] = nav["is_filled"].astype(int)
    nav = nav.rename(columns={"date": "date_key"})
    nav.to_sql("fact_nav", engine, if_exists="append", index=False)
    print(f"  Loaded fact_nav: {len(nav)} rows.")

    # ---- 5. fact_transactions ------------------------------------------------------
    tx = pd.read_csv(PROCESSED["investor_transactions"])
    tx = tx.rename(columns={"transaction_date": "date_key"})
    tx.to_sql("fact_transactions", engine, if_exists="append", index=False)
    print(f"  Loaded fact_transactions: {len(tx)} rows.")

    # ---- 6. fact_performance ------------------------------------------------------
    perf = pd.read_csv(PROCESSED["scheme_performance"])
    perf_cols = [
        "amfi_code", "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
        "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio", "sortino_ratio",
        "std_dev_ann_pct", "max_drawdown_pct", "aum_crore", "expense_ratio_pct",
        "morningstar_rating", "risk_grade", "anomaly_flags",
    ]
    perf[perf_cols].to_sql("fact_performance", engine, if_exists="append", index=False)
    print(f"  Loaded fact_performance: {len(perf)} rows.")

    # ---- 7. fact_aum ------------------------------------------------------------------
    aum = pd.read_csv(PROCESSED["aum_by_fund_house"])
    aum = aum.rename(columns={"date": "date_key"})
    aum.to_sql("fact_aum", engine, if_exists="append", index=False)
    print(f"  Loaded fact_aum: {len(aum)} rows.")

    # ---- 8. Supporting reference tables --------------------------------------------------
    sip = pd.read_csv(PROCESSED["monthly_sip_inflows"])
    sip.to_sql("monthly_sip_inflows", engine, if_exists="append", index=False)
    print(f"  Loaded monthly_sip_inflows: {len(sip)} rows.")

    cat = pd.read_csv(PROCESSED["category_inflows"])
    cat.to_sql("category_inflows", engine, if_exists="append", index=False)
    print(f"  Loaded category_inflows: {len(cat)} rows.")

    folio = pd.read_csv(PROCESSED["industry_folio_count"])
    folio.to_sql("industry_folio_count", engine, if_exists="append", index=False)
    print(f"  Loaded industry_folio_count: {len(folio)} rows.")

    holdings = pd.read_csv(PROCESSED["portfolio_holdings"])
    holdings.to_sql("portfolio_holdings", engine, if_exists="append", index=False)
    print(f"  Loaded portfolio_holdings: {len(holdings)} rows.")

    bench = pd.read_csv(PROCESSED["benchmark_indices"])
    bench = bench.rename(columns={"date": "date_key"})
    bench.to_sql("benchmark_indices", engine, if_exists="append", index=False)
    print(f"  Loaded benchmark_indices: {len(bench)} rows.")

    # ---- 9. Verify row counts match source CSVs --------------------------------------------
    log_section("VERIFY: row counts (SQLite vs cleaned CSV)")
    checks = [
        ("dim_fund", len(fund_master)),
        ("fact_nav", len(nav)),
        ("fact_transactions", len(tx)),
        ("fact_performance", len(perf)),
        ("fact_aum", len(aum)),
        ("monthly_sip_inflows", len(sip)),
        ("category_inflows", len(cat)),
        ("industry_folio_count", len(folio)),
        ("portfolio_holdings", len(holdings)),
        ("benchmark_indices", len(bench)),
        ("dim_date", len(dim_date)),
    ]
    all_ok = True
    with engine.connect() as conn:
        for table, expected in checks:
            actual = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            status = "OK" if actual == expected else "MISMATCH"
            if actual != expected:
                all_ok = False
            print(f"  {table:25s} expected={expected:7d}  actual={actual:7d}  [{status}]")

    print(f"\n{'All row counts match.' if all_ok else 'WARNING: some row counts did not match -- see above.'}")
    print(f"\nDatabase ready at: {DB_PATH}")


if __name__ == "__main__":
    main()