"""
clean_nav.py
------------
Day 2 Task: Clean 02_nav_history.csv

Per the task brief:
  - Parse dates to datetime
  - Sort by amfi_code + date
  - Forward-fill missing NAV for holidays/weekends
  - Remove duplicates
  - Validate NAV > 0

Source data note (confirmed by inspection): the raw file only contains
business-day rows (Mon-Fri), no weekend rows at all, and no missing
weekdays within each fund's date range. "Forward-filling missing NAV for
holidays/weekends" therefore means: build a complete CALENDAR (every day,
including weekends) spanning each fund's min->max date, and forward-fill
the last known NAV onto the days the market was closed. This gives you
one NAV value per fund per calendar day, which is what you'll want later
for joining against daily investor transactions.

Output: data/processed/02_nav_history.csv
  columns: amfi_code, date, nav, is_filled
    is_filled = True for rows that did NOT have a NAV in the source file
                (i.e. they were forward-filled for a non-trading day).

Run:
    python clean_nav.py
"""

import pandas as pd

from common import RAW, PROCESSED, NAV_HISTORY_COLS, log_section


def main():
    log_section("CLEAN: nav_history")

    df = pd.read_csv(RAW["nav_history"])
    print(f"Loaded {RAW['nav_history'].name}: {df.shape[0]} rows, columns={list(df.columns)}")

    missing_cols = [c for c in NAV_HISTORY_COLS if c not in df.columns]
    if missing_cols:
        raise KeyError(
            f"nav_history.csv is missing expected column(s) {missing_cols}. "
            f"Actual columns: {list(df.columns)}. Update NAV_HISTORY_COLS in common.py "
            f"if the real column name has changed."
        )

    # ---- 1. Parse dates to datetime -------------------------------------
    before = len(df)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    bad_dates = df["date"].isna().sum()
    if bad_dates:
        print(f"  WARNING: {bad_dates} row(s) had unparseable dates and will be dropped.")
        df = df.dropna(subset=["date"])

    # ---- 2. Remove duplicates --------------------------------------------
    # Exact duplicate rows
    exact_dupes = df.duplicated().sum()
    df = df.drop_duplicates()
    # Duplicate (amfi_code, date) pairs with possibly different NAV values:
    # keep the last occurrence (assume later row = more authoritative correction)
    key_dupes = df.duplicated(subset=["amfi_code", "date"], keep="last").sum()
    df = df.drop_duplicates(subset=["amfi_code", "date"], keep="last")
    print(f"  Removed {exact_dupes} exact duplicate row(s) and "
          f"{key_dupes} duplicate (amfi_code, date) row(s).")

    # ---- 3. Validate NAV > 0 ----------------------------------------------
    invalid_nav = df[df["nav"] <= 0]
    if len(invalid_nav):
        print(f"  WARNING: {len(invalid_nav)} row(s) have nav <= 0 and will be dropped:")
        print(invalid_nav.head(10).to_string(index=False))
        df = df[df["nav"] > 0]
    else:
        print("  NAV validation: all values > 0. OK.")

    # ---- 4. Sort by amfi_code + date --------------------------------------
    df = df.sort_values(["amfi_code", "date"]).reset_index(drop=True)

    # ---- 5. Forward-fill onto a complete calendar (incl. weekends/holidays)
    print("  Building complete daily calendar per fund and forward-filling NAV ...")
    filled_frames = []
    for code, grp in df.groupby("amfi_code", sort=False):
        grp = grp.sort_values("date")
        full_range = pd.date_range(grp["date"].min(), grp["date"].max(), freq="D")
        grp_indexed = grp.set_index("date").reindex(full_range)
        grp_indexed["is_filled"] = grp_indexed["nav"].isna()
        grp_indexed["nav"] = grp_indexed["nav"].ffill()
        grp_indexed["amfi_code"] = code
        grp_indexed = grp_indexed.reset_index().rename(columns={"index": "date"})
        filled_frames.append(grp_indexed[["amfi_code", "date", "nav", "is_filled"]])

    out = pd.concat(filled_frames, ignore_index=True)
    out = out.sort_values(["amfi_code", "date"]).reset_index(drop=True)

    n_filled = int(out["is_filled"].sum())
    print(f"  Calendar expanded from {len(df)} trading-day rows to {len(out)} calendar-day rows "
          f"({n_filled} forward-filled non-trading-day rows).")

    # Final sanity check: no NAV should still be null (only possible if a fund's
    # very first calendar day had no source value at all, which shouldn't happen).
    still_null = out["nav"].isna().sum()
    if still_null:
        print(f"  WARNING: {still_null} row(s) still have null NAV after forward-fill "
              f"(this means a fund's first available date had no prior value to fill from).")

    out_path = PROCESSED["nav_history"]
    out.to_csv(out_path, index=False)
    print(f"\nSaved cleaned file -> {out_path} ({out.shape[0]} rows, {out.shape[1]} columns)")
    print(f"Columns: {list(out.columns)}")


if __name__ == "__main__":
    main()