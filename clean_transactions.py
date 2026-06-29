"""
clean_transactions.py
----------------------
Day 2 Task: Clean 08_investor_transactions.csv

Per the task brief:
  - Standardise transaction_type values (SIP / Lumpsum / Redemption)
  - Validate amount > 0
  - Fix date formats
  - Check KYC status enum values

Output: data/processed/08_investor_transactions.csv

Run:
    python clean_transactions.py
"""

import pandas as pd

from common import (
    RAW, PROCESSED, INVESTOR_TRANSACTIONS_COLS,
    VALID_TRANSACTION_TYPES, VALID_KYC_STATUS, log_section,
)


def main():
    log_section("CLEAN: investor_transactions")

    df = pd.read_csv(RAW["investor_transactions"])
    print(f"Loaded {RAW['investor_transactions'].name}: {df.shape[0]} rows, "
          f"columns={list(df.columns)}")

    missing_cols = [c for c in INVESTOR_TRANSACTIONS_COLS if c not in df.columns]
    if missing_cols:
        raise KeyError(
            f"investor_transactions.csv is missing expected column(s) {missing_cols}. "
            f"Actual columns: {list(df.columns)}. Update INVESTOR_TRANSACTIONS_COLS in "
            f"common.py if the real column name has changed."
        )

    before = len(df)

    # ---- 1. Fix date formats ----------------------------------------------
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    bad_dates = df["transaction_date"].isna().sum()
    if bad_dates:
        print(f"  WARNING: {bad_dates} row(s) had unparseable transaction_date and "
              f"will be dropped.")
        df = df.dropna(subset=["transaction_date"])

    # ---- 2. Standardise transaction_type -----------------------------------
    df["transaction_type"] = df["transaction_type"].astype(str).str.strip().str.title()
    # Normalise common case/typo variants onto the 3 canonical values
    type_fix_map = {
        "Sip": "SIP", "SIP": "SIP",
        "Lumpsum": "Lumpsum", "Lump Sum": "Lumpsum",
        "Redemption": "Redemption", "Redeem": "Redemption",
    }
    df["transaction_type"] = df["transaction_type"].replace(type_fix_map)
    bad_types = df[~df["transaction_type"].isin(VALID_TRANSACTION_TYPES)]
    if len(bad_types):
        print(f"  WARNING: {len(bad_types)} row(s) have a transaction_type outside "
              f"{VALID_TRANSACTION_TYPES} after standardisation: "
              f"{bad_types['transaction_type'].unique().tolist()}. These rows will be dropped.")
        df = df[df["transaction_type"].isin(VALID_TRANSACTION_TYPES)]
    else:
        print(f"  transaction_type values OK: {sorted(df['transaction_type'].unique())}")

    # ---- 3. Validate amount > 0 ---------------------------------------------
    invalid_amt = df[df["amount_inr"] <= 0]
    if len(invalid_amt):
        print(f"  WARNING: {len(invalid_amt)} row(s) have amount_inr <= 0 and will be dropped.")
        df = df[df["amount_inr"] > 0]
    else:
        print("  amount_inr validation: all values > 0. OK.")

    # ---- 4. Check KYC status enum values -------------------------------------
    df["kyc_status"] = df["kyc_status"].astype(str).str.strip().str.title()
    bad_kyc = df[~df["kyc_status"].isin(VALID_KYC_STATUS)]
    if len(bad_kyc):
        print(f"  WARNING: {len(bad_kyc)} row(s) have a kyc_status outside "
              f"{VALID_KYC_STATUS}: {bad_kyc['kyc_status'].unique().tolist()}. "
              f"Flagging as 'Unknown' rather than dropping (transaction itself is still valid).")
        df.loc[~df["kyc_status"].isin(VALID_KYC_STATUS), "kyc_status"] = "Unknown"
    else:
        print(f"  kyc_status values OK: {sorted(df['kyc_status'].unique())}")

    # ---- 5. De-duplicate ------------------------------------------------------
    exact_dupes = df.duplicated().sum()
    df = df.drop_duplicates()
    print(f"  Removed {exact_dupes} exact duplicate row(s).")

    df = df.sort_values(["transaction_date", "investor_id"]).reset_index(drop=True)

    print(f"\n  Rows: {before} -> {len(df)} after cleaning "
          f"({before - len(df)} removed).")

    out_path = PROCESSED["investor_transactions"]
    df.to_csv(out_path, index=False)
    print(f"Saved cleaned file -> {out_path} ({df.shape[0]} rows, {df.shape[1]} columns)")
    print(f"Columns: {list(df.columns)}")


if __name__ == "__main__":
    main()