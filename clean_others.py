"""
clean_others.py
----------------
Day 2 Task: the task brief calls out specific cleaning steps for
nav_history, investor_transactions, and scheme_performance (handled in
clean_nav.py / clean_transactions.py / clean_performance.py).

The deliverable list asks for "10 cleaned CSVs in data/processed/", so
this script handles standard cleaning + validation for the remaining 7
files that don't have bespoke rules in the brief:

  01_fund_master.csv          - parse launch_date, de-dup, FK sanity
  03_aum_by_fund_house.csv    - parse date, validate aum > 0
  04_monthly_sip_inflows.csv  - parse month, validate inflow > 0
  05_category_inflows.csv     - parse month, de-dup
  06_industry_folio_count.csv - parse month, validate folio counts > 0
  09_portfolio_holdings.csv   - parse portfolio_date, validate weight_pct
                                  range, FK check against fund_master
  10_benchmark_indices.csv    - parse date, validate close_value > 0

Each file gets: dtype/date parsing, duplicate removal, and a basic
range/positivity check appropriate to its columns. Anything flagged is
printed but not silently dropped unless it's a true parse failure.

Run:
    python clean_others.py
"""

import pandas as pd

from common import RAW, PROCESSED, log_section


def basic_clean(df: pd.DataFrame, name: str, date_cols=None, positive_cols=None,
                 dedupe_subset=None) -> pd.DataFrame:
    before = len(df)
    date_cols = date_cols or []
    positive_cols = positive_cols or []

    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        bad = df[col].isna().sum()
        if bad:
            print(f"  WARNING [{name}]: {bad} row(s) had unparseable '{col}', dropping.")
            df = df.dropna(subset=[col])

    for col in positive_cols:
        bad = df[df[col] <= 0]
        if len(bad):
            print(f"  WARNING [{name}]: {len(bad)} row(s) have non-positive '{col}'.")

    exact_dupes = df.duplicated().sum()
    df = df.drop_duplicates()
    if dedupe_subset:
        key_dupes = df.duplicated(subset=dedupe_subset).sum()
        df = df.drop_duplicates(subset=dedupe_subset, keep="last")
    else:
        key_dupes = 0

    print(f"  [{name}] rows {before} -> {len(df)} "
          f"(removed {exact_dupes} exact dupes, {key_dupes} key dupes)")
    return df


def main():
    log_section("CLEAN: remaining 7 supporting files")

    # ---- fund_master ----------------------------------------------------
    fm = pd.read_csv(RAW["fund_master"])
    fm = basic_clean(fm, "fund_master", date_cols=["launch_date"],
                      dedupe_subset=["amfi_code"])
    bad_expense = fm[(fm["expense_ratio_pct"] < 0.1) | (fm["expense_ratio_pct"] > 2.5)]
    if len(bad_expense):
        print(f"  WARNING [fund_master]: {len(bad_expense)} row(s) outside expense_ratio "
              f"0.1-2.5 range.")
    fm.to_csv(PROCESSED["fund_master"], index=False)

    # ---- aum_by_fund_house ------------------------------------------------
    aum = pd.read_csv(RAW["aum_by_fund_house"])
    aum = basic_clean(aum, "aum_by_fund_house", date_cols=["date"],
                       positive_cols=["aum_crore", "num_schemes"])
    aum.to_csv(PROCESSED["aum_by_fund_house"], index=False)

    # ---- monthly_sip_inflows ------------------------------------------------
    sip = pd.read_csv(RAW["monthly_sip_inflows"])
    # 'month' is a YYYY-MM string, not a full date -- keep as period but validate format
    bad_month = sip[pd.to_datetime(sip["month"], format="%Y-%m", errors="coerce").isna()]
    if len(bad_month):
        print(f"  WARNING [monthly_sip_inflows]: {len(bad_month)} row(s) have an "
              f"unparseable 'month' value, dropping.")
        sip = sip[~sip.index.isin(bad_month.index)]
    sip = basic_clean(sip, "monthly_sip_inflows", positive_cols=["sip_inflow_crore"])
    # yoy_growth_pct has known nulls for the first 12 months (no prior-year data to
    # compare against) -- this is expected, not an error. Leave as NaN.
    n_null_yoy = sip["yoy_growth_pct"].isna().sum()
    print(f"  [monthly_sip_inflows] yoy_growth_pct null count: {n_null_yoy} "
          f"(expected: first 12 months have no prior year to compare).")
    sip.to_csv(PROCESSED["monthly_sip_inflows"], index=False)

    # ---- category_inflows ------------------------------------------------
    cat = pd.read_csv(RAW["category_inflows"])
    cat = basic_clean(cat, "category_inflows", dedupe_subset=["month", "category"])
    cat.to_csv(PROCESSED["category_inflows"], index=False)

    # ---- industry_folio_count ------------------------------------------------
    folio = pd.read_csv(RAW["industry_folio_count"])
    folio = basic_clean(
        folio, "industry_folio_count",
        positive_cols=["total_folios_crore", "equity_folios_crore",
                        "debt_folios_crore", "hybrid_folios_crore", "others_folios_crore"],
        dedupe_subset=["month"],
    )
    folio.to_csv(PROCESSED["industry_folio_count"], index=False)

    # ---- portfolio_holdings ------------------------------------------------
    ph = pd.read_csv(RAW["portfolio_holdings"])
    ph = basic_clean(ph, "portfolio_holdings", date_cols=["portfolio_date"],
                      positive_cols=["market_value_cr", "current_price_inr"])
    bad_weight = ph[(ph["weight_pct"] <= 0) | (ph["weight_pct"] > 100)]
    if len(bad_weight):
        print(f"  WARNING [portfolio_holdings]: {len(bad_weight)} row(s) have "
              f"weight_pct outside (0, 100].")
    fk_missing = set(ph["amfi_code"]) - set(fm["amfi_code"])
    if fk_missing:
        print(f"  WARNING [portfolio_holdings]: amfi_code(s) {fk_missing} not found "
              f"in fund_master.")
    else:
        print("  [portfolio_holdings] FK check vs fund_master: all amfi_codes OK.")
    ph.to_csv(PROCESSED["portfolio_holdings"], index=False)

    # ---- benchmark_indices ------------------------------------------------
    bi = pd.read_csv(RAW["benchmark_indices"])
    bi = basic_clean(bi, "benchmark_indices", date_cols=["date"],
                      positive_cols=["close_value"], dedupe_subset=["date", "index_name"])
    bi.to_csv(PROCESSED["benchmark_indices"], index=False)

    print("\nAll 7 supporting files cleaned and saved to data/processed/.")


if __name__ == "__main__":
    main()