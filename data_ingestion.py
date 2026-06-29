"""
data_ingestion.py
------------------
Day 1 Task: Project Setup + Data Ingestion (ETL)

What this script does:
1. Loads every CSV found in data/raw/ using pandas.
2. For each file, prints .shape, .dtypes, and .head(), and flags basic
   anomalies (nulls, duplicate rows, fully-empty columns).
3. Looks for a "fund master" style file and a "nav history" style file
   among the loaded CSVs (by filename, then by column signature) and:
      a. Prints unique fund houses, categories, sub-categories, risk grades
         from the fund master file.
      b. Validates that every AMFI/scheme code in fund_master also exists
         in nav_history (and reports any codes that don't match either way).
4. Writes a consolidated data quality summary to reports/day1_data_quality_summary.md

HOW TO USE THIS WITH YOUR OWN FILES:
- Drop all 10 provided CSVs into data/raw/ before running this script.
- Column names vary a lot between mutual-fund datasets, so this script tries
  several common aliases (see COLUMN_ALIASES below) to auto-detect the right
  columns. If it can't find a column it needs, it will print a clear warning
  telling you which file/column to check manually -- just open that CSV,
  confirm the real column name, and add it to COLUMN_ALIASES.

Run:
    python data_ingestion.py
"""

from pathlib import Path
import sys

import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

RAW_DIR = Path(__file__).resolve().parent / "data" / "raw"
REPORTS_DIR = Path(__file__).resolve().parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Common column-name aliases across mutual fund datasets (AMFI / NAVAll / etc.)
# Add to these lists if your actual file uses a different name.
COLUMN_ALIASES = {
    "scheme_code": ["scheme_code", "amfi_code", "amfi_scheme_code", "code",
                     "scheme code", "amfi code", "schemecode"],
    "fund_house": ["fund_house", "amc", "mutual_fund_family", "fund house",
                   "amc_name", "fundhouse"],
    "category": ["category", "scheme_category", "fund_category", "category_name"],
    "sub_category": ["sub_category", "subcategory", "scheme_sub_category",
                      "sub category", "sub-category"],
    "risk_grade": ["risk_grade", "risk", "risk_level", "riskometer",
                    "risk grade", "risk_category"],
    "nav": ["nav", "net_asset_value"],
    "date": ["date", "nav_date"],
}

# Filename hints used to guess which CSV is which (case-insensitive substring match)
FUND_MASTER_HINTS = ["fund_master", "fundmaster", "fund master", "scheme_master", "master"]
NAV_HISTORY_HINTS = ["nav_history", "navhistory", "nav history", "nav"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_column(df: pd.DataFrame, logical_name: str):
    """Return the actual column name in df matching a logical alias, or None."""
    candidates = COLUMN_ALIASES.get(logical_name, [logical_name])
    lower_map = {c.lower().strip(): c for c in df.columns}
    for cand in candidates:
        if cand in lower_map:
            return lower_map[cand]
    return None


def guess_file_role(filename: str, hints: list[str]) -> bool:
    name = filename.lower()
    return any(h in name for h in hints)


def profile_dataframe(name: str, df: pd.DataFrame, report_lines: list[str]):
    """Print + record shape/dtypes/head/anomalies for a single dataframe."""
    print(f"\n{'=' * 70}\nFILE: {name}\n{'=' * 70}")
    print(f"Shape: {df.shape}")
    print("\nDtypes:")
    print(df.dtypes)
    print("\nHead:")
    print(df.head())

    null_counts = df.isnull().sum()
    cols_with_nulls = null_counts[null_counts > 0]
    dup_count = df.duplicated().sum()
    empty_cols = [c for c in df.columns if df[c].isnull().all()]

    print("\nAnomaly check:")
    if cols_with_nulls.empty:
        print("  - No null values found.")
    else:
        print(f"  - Columns with nulls:\n{cols_with_nulls}")
    print(f"  - Duplicate rows: {dup_count}")
    if empty_cols:
        print(f"  - Fully empty columns: {empty_cols}")

    report_lines.append(f"### {name}")
    report_lines.append(f"- Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    report_lines.append(f"- Duplicate rows: {dup_count}")
    if not cols_with_nulls.empty:
        null_str = ", ".join(f"{c} ({n})" for c, n in cols_with_nulls.items())
        report_lines.append(f"- Columns with nulls: {null_str}")
    else:
        report_lines.append("- Columns with nulls: none")
    if empty_cols:
        report_lines.append(f"- Fully empty columns: {empty_cols}")
    report_lines.append("")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    report_lines = ["# Day 1 - Data Quality Summary", ""]

    csv_files = sorted(RAW_DIR.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in {RAW_DIR}.")
        print("Copy your 10 provided datasets into data/raw/ and re-run this script.")
        sys.exit(1)

    print(f"Found {len(csv_files)} CSV file(s) in {RAW_DIR}:")
    for f in csv_files:
        print(f"  - {f.name}")

    dataframes = {}
    for f in csv_files:
        try:
            df = pd.read_csv(f)
        except Exception as exc:
            print(f"  ERROR reading {f.name}: {exc}")
            report_lines.append(f"### {f.name}\n- FAILED TO LOAD: {exc}\n")
            continue
        dataframes[f.name] = df
        profile_dataframe(f.name, df, report_lines)

    # ------------------------------------------------------------------
    # Identify fund_master and nav_history files
    # ------------------------------------------------------------------
    fund_master_name = next(
        (n for n in dataframes if guess_file_role(n, FUND_MASTER_HINTS)), None
    )
    nav_history_name = next(
        (n for n in dataframes if guess_file_role(n, NAV_HISTORY_HINTS)), None
    )

    report_lines.append("## Fund Master Exploration")
    if fund_master_name is None:
        msg = ("Could not auto-detect a fund_master file by filename. "
               "Rename the relevant CSV to include 'fund_master' or 'master', "
               "or adjust FUND_MASTER_HINTS in this script.")
        print(f"\nWARNING: {msg}")
        report_lines.append(f"- WARNING: {msg}")
    else:
        fm = dataframes[fund_master_name]
        print(f"\nUsing '{fund_master_name}' as fund master file.")
        report_lines.append(f"- Detected fund master file: `{fund_master_name}`")

        for logical in ["fund_house", "category", "sub_category", "risk_grade"]:
            col = find_column(fm, logical)
            if col is None:
                msg = (f"Could not find a column for '{logical}' in {fund_master_name}. "
                       f"Check the real column name and add it to COLUMN_ALIASES['{logical}'].")
                print(f"  WARNING: {msg}")
                report_lines.append(f"- WARNING: {msg}")
                continue
            uniques = sorted(fm[col].dropna().unique().tolist())
            print(f"\nUnique {logical} ({col}) [{len(uniques)}]: {uniques}")
            report_lines.append(f"- Unique **{logical}** (`{col}`), {len(uniques)} values: "
                                 f"{', '.join(map(str, uniques))}")

    # ------------------------------------------------------------------
    # AMFI scheme code validation: fund_master codes must exist in nav_history
    # ------------------------------------------------------------------
    report_lines.append("\n## AMFI Scheme Code Validation")
    if fund_master_name is None or nav_history_name is None:
        msg = ("Skipped AMFI code validation because fund_master and/or "
               "nav_history file could not be auto-detected. "
               f"fund_master_name={fund_master_name}, nav_history_name={nav_history_name}")
        print(f"\nWARNING: {msg}")
        report_lines.append(f"- WARNING: {msg}")
    else:
        fm = dataframes[fund_master_name]
        nh = dataframes[nav_history_name]

        fm_code_col = find_column(fm, "scheme_code")
        nh_code_col = find_column(nh, "scheme_code")

        if fm_code_col is None or nh_code_col is None:
            msg = (f"Could not find a scheme_code column in one of the files "
                   f"(fund_master col={fm_code_col}, nav_history col={nh_code_col}). "
                   f"Check real column names and update COLUMN_ALIASES['scheme_code'].")
            print(f"\nWARNING: {msg}")
            report_lines.append(f"- WARNING: {msg}")
        else:
            fm_codes = set(fm[fm_code_col].dropna().astype(str).str.strip())
            nh_codes = set(nh[nh_code_col].dropna().astype(str).str.strip())

            missing_in_nav = fm_codes - nh_codes
            missing_in_master = nh_codes - fm_codes
            matched = fm_codes & nh_codes

            print(f"\nfund_master codes: {len(fm_codes)} | nav_history codes: {len(nh_codes)}")
            print(f"Matched: {len(matched)}")
            print(f"In fund_master but missing from nav_history: {len(missing_in_nav)}")
            if missing_in_nav:
                print(f"  {sorted(missing_in_nav)[:20]}{' ...' if len(missing_in_nav) > 20 else ''}")
            print(f"In nav_history but missing from fund_master: {len(missing_in_master)}")
            if missing_in_master:
                print(f"  {sorted(missing_in_master)[:20]}{' ...' if len(missing_in_master) > 20 else ''}")

            report_lines.append(f"- fund_master codes: {len(fm_codes)}")
            report_lines.append(f"- nav_history codes: {len(nh_codes)}")
            report_lines.append(f"- Matched codes: {len(matched)}")
            report_lines.append(
                f"- In fund_master but missing from nav_history: {len(missing_in_nav)}"
            )
            report_lines.append(
                f"- In nav_history but missing from fund_master: {len(missing_in_master)}"
            )
            if not missing_in_nav and not missing_in_master:
                report_lines.append("- Result: All AMFI codes are fully consistent "
                                     "between fund_master and nav_history.")
            else:
                report_lines.append("- Result: Inconsistencies found -- see lists above "
                                     "(or re-run the script to print full lists to console).")

    # ------------------------------------------------------------------
    # Write summary report
    # ------------------------------------------------------------------
    summary_path = REPORTS_DIR / "day1_data_quality_summary.md"
    summary_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n\nData quality summary written to: {summary_path}")


if __name__ == "__main__":
    main()