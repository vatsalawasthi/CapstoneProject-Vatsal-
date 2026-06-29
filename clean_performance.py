"""
clean_performance.py
---------------------
Day 2 Task: Clean 07_scheme_performance.csv

Per the task brief:
  - Validate all return values are numeric
  - Flag anomalies
  - Check expense_ratio range (0.1% - 2.5%)

Output: data/processed/07_scheme_performance.csv
  An extra column `anomaly_flags` is added listing any anomalies found for
  that row (empty string if none). Rows are NOT dropped for anomalies --
  performance stats are real reported figures, not necessarily "wrong",
  so we flag rather than silently delete. Rows are dropped only for
  genuinely broken data (non-numeric returns, missing amfi_code).

Run:
    python clean_performance.py
"""

import pandas as pd

from common import (
    RAW, PROCESSED, SCHEME_PERFORMANCE_COLS,
    EXPENSE_RATIO_MIN_PCT, EXPENSE_RATIO_MAX_PCT, log_section,
)

RETURN_COLS = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "benchmark_3yr_pct"]


def main():
    log_section("CLEAN: scheme_performance")

    df = pd.read_csv(RAW["scheme_performance"])
    print(f"Loaded {RAW['scheme_performance'].name}: {df.shape[0]} rows, "
          f"columns={list(df.columns)}")

    missing_cols = [c for c in SCHEME_PERFORMANCE_COLS if c not in df.columns]
    if missing_cols:
        raise KeyError(
            f"scheme_performance.csv is missing expected column(s) {missing_cols}. "
            f"Actual columns: {list(df.columns)}. Update SCHEME_PERFORMANCE_COLS in "
            f"common.py if the real column name has changed."
        )

    before = len(df)

    # ---- 1. Validate all return values are numeric --------------------------
    for col in RETURN_COLS:
        non_numeric_before = df[col].apply(lambda v: not isinstance(v, (int, float))).sum()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        broke = df[col].isna().sum()
        if broke:
            print(f"  WARNING: {broke} row(s) in '{col}' were non-numeric and "
                  f"coerced to NaN.")

    broken_rows = df[RETURN_COLS].isna().any(axis=1)
    if broken_rows.sum():
        print(f"  Dropping {broken_rows.sum()} row(s) with unrecoverable non-numeric "
              f"return values.")
        df = df[~broken_rows].copy()
    else:
        print(f"  All return columns ({RETURN_COLS}) are numeric. OK.")

    # ---- 2. Flag anomalies -----------------------------------------------------
    anomaly_flags = pd.Series([""] * len(df), index=df.index)

    def add_flag(mask, label):
        nonlocal anomaly_flags
        anomaly_flags.loc[mask] = anomaly_flags.loc[mask].apply(
            lambda existing: f"{existing};{label}" if existing else label
        )

    # expense ratio out of stated valid range
    bad_expense = (df["expense_ratio_pct"] < EXPENSE_RATIO_MIN_PCT) | \
                   (df["expense_ratio_pct"] > EXPENSE_RATIO_MAX_PCT)
    add_flag(bad_expense, f"expense_ratio_outside_{EXPENSE_RATIO_MIN_PCT}-{EXPENSE_RATIO_MAX_PCT}pct")

    # negative AUM or zero AUM
    add_flag(df["aum_crore"] <= 0, "aum_non_positive")

    # max_drawdown_pct should be <= 0 (it's a drawdown)
    add_flag(df["max_drawdown_pct"] > 0, "positive_max_drawdown")

    # std_dev (volatility) should not be negative
    add_flag(df["std_dev_ann_pct"] < 0, "negative_std_dev")

    # sharpe/sortino sanity: extreme outliers (very loose bounds, just a flag)
    add_flag(df["sharpe_ratio"].abs() > 5, "sharpe_ratio_extreme_outlier")

    # morningstar_rating should be an integer 1-5
    add_flag(~df["morningstar_rating"].between(1, 5), "morningstar_rating_out_of_range")

    df["anomaly_flags"] = anomaly_flags
    n_flagged = (df["anomaly_flags"] != "").sum()
    print(f"  Anomaly scan complete: {n_flagged} of {len(df)} row(s) flagged "
          f"(rows are kept, not dropped -- see anomaly_flags column).")
    if n_flagged:
        print(df.loc[df["anomaly_flags"] != "", ["amfi_code", "scheme_name", "anomaly_flags"]]
              .to_string(index=False))

    # ---- 3. Check expense_ratio range explicitly (reported separately too) ----
    print(f"\n  expense_ratio_pct range in file: "
          f"{df['expense_ratio_pct'].min()} - {df['expense_ratio_pct'].max()} "
          f"(valid range: {EXPENSE_RATIO_MIN_PCT}-{EXPENSE_RATIO_MAX_PCT})")

    # ---- 4. De-duplicate --------------------------------------------------------
    exact_dupes = df.duplicated().sum()
    df = df.drop_duplicates()
    dup_codes = df.duplicated(subset=["amfi_code"]).sum()
    if dup_codes:
        print(f"  WARNING: {dup_codes} duplicate amfi_code row(s) found; keeping last.")
        df = df.drop_duplicates(subset=["amfi_code"], keep="last")
    print(f"  Removed {exact_dupes} exact duplicate row(s).")

    df = df.sort_values("amfi_code").reset_index(drop=True)

    print(f"\n  Rows: {before} -> {len(df)} after cleaning ({before - len(df)} removed).")

    out_path = PROCESSED["scheme_performance"]
    df.to_csv(out_path, index=False)
    print(f"Saved cleaned file -> {out_path} ({df.shape[0]} rows, {df.shape[1]} columns)")
    print(f"Columns: {list(df.columns)}")


if __name__ == "__main__":
    main()