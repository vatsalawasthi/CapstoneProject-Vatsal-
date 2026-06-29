"""
common.py
---------
Shared paths + constants used by every Day 2 script:
  clean_nav.py, clean_transactions.py, clean_performance.py,
  build_schema.py, load_to_sqlite.py, run_queries.py, build_data_dictionary.py

Column names below were confirmed directly against the real Day 1 CSVs
(data/raw/01_fund_master.csv ... 10_benchmark_indices.csv) -- no alias
guessing needed, since the files were already inspected.

If you ever swap in a different export of these files and a column name
has changed, the cleaning scripts will raise a clear KeyError naming the
missing column -- just update the relevant *_COLS list below.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (match the repo layout from Day 1)
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
REPORTS_DIR = ROOT_DIR / "reports"
SQL_DIR = ROOT_DIR / "sql"
DB_PATH = ROOT_DIR / "bluestock_mf.db"

for d in (PROCESSED_DIR, REPORTS_DIR, SQL_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Raw file names (confirmed against your actual data/raw/ folder)
# ---------------------------------------------------------------------------

RAW = {
    "fund_master": RAW_DIR / "01_fund_master.csv",
    "nav_history": RAW_DIR / "02_nav_history.csv",
    "aum_by_fund_house": RAW_DIR / "03_aum_by_fund_house.csv",
    "monthly_sip_inflows": RAW_DIR / "04_monthly_sip_inflows.csv",
    "category_inflows": RAW_DIR / "05_category_inflows.csv",
    "industry_folio_count": RAW_DIR / "06_industry_folio_count.csv",
    "scheme_performance": RAW_DIR / "07_scheme_performance.csv",
    "investor_transactions": RAW_DIR / "08_investor_transactions.csv",
    "portfolio_holdings": RAW_DIR / "09_portfolio_holdings.csv",
    "benchmark_indices": RAW_DIR / "10_benchmark_indices.csv",
}

# Processed (cleaned) output paths -- one per raw file, same logical keys
PROCESSED = {key: PROCESSED_DIR / path.name for key, path in RAW.items()}

# ---------------------------------------------------------------------------
# Confirmed real column names (from direct inspection of the CSVs)
# ---------------------------------------------------------------------------

FUND_MASTER_COLS = [
    "amfi_code", "fund_house", "scheme_name", "category", "sub_category",
    "plan", "launch_date", "benchmark", "expense_ratio_pct", "exit_load_pct",
    "min_sip_amount", "min_lumpsum_amount", "fund_manager", "risk_category",
    "sebi_category_code",
]

NAV_HISTORY_COLS = ["amfi_code", "date", "nav"]

SCHEME_PERFORMANCE_COLS = [
    "amfi_code", "scheme_name", "fund_house", "category", "plan",
    "return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "benchmark_3yr_pct",
    "alpha", "beta", "sharpe_ratio", "sortino_ratio", "std_dev_ann_pct",
    "max_drawdown_pct", "aum_crore", "expense_ratio_pct", "morningstar_rating",
    "risk_grade",
]

INVESTOR_TRANSACTIONS_COLS = [
    "investor_id", "transaction_date", "amfi_code", "transaction_type",
    "amount_inr", "state", "city", "city_tier", "age_group", "gender",
    "annual_income_lakh", "payment_mode", "kyc_status",
]

PORTFOLIO_HOLDINGS_COLS = [
    "amfi_code", "stock_symbol", "stock_name", "sector", "weight_pct",
    "market_value_cr", "current_price_inr", "portfolio_date",
]

BENCHMARK_INDICES_COLS = ["date", "index_name", "close_value"]

# Valid enum values confirmed from the real data (used for validation)
VALID_TRANSACTION_TYPES = {"SIP", "Lumpsum", "Redemption"}
VALID_KYC_STATUS = {"Verified", "Pending"}
EXPENSE_RATIO_MIN_PCT = 0.1
EXPENSE_RATIO_MAX_PCT = 2.5


def log_section(title: str):
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")