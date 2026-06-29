# Data Dictionary — Bluestock Mutual Fund Capstone

**Database:** `bluestock_mf.db` (SQLite)
**Generated for:** Day 2 — Data Cleaning + SQL Database Design
**Schema type:** Star schema (2 dimensions, 4 fact tables, 5 supporting reference tables)

---

## 1. Schema overview

| Table | Role | Grain (1 row =) | Row count |
|---|---|---|---|
| `dim_fund` | Dimension | 1 mutual fund scheme | 40 |
| `dim_date` | Dimension | 1 calendar day | 1,612 (2022-01-01 → 2026-05-31) |
| `fact_nav` | Fact | 1 fund's NAV on 1 day | 64,320 |
| `fact_transactions` | Fact | 1 investor transaction | 32,778 |
| `fact_performance` | Fact (snapshot) | 1 fund's trailing performance snapshot | 40 |
| `fact_aum` | Fact | 1 fund house's AUM on 1 reporting date | 90 |
| `monthly_sip_inflows` | Reference | 1 calendar month, industry-wide SIP stats | 48 |
| `category_inflows` | Reference | 1 month × 1 fund category | 144 |
| `industry_folio_count` | Reference | 1 calendar month, industry-wide folio stats | 21 |
| `portfolio_holdings` | Reference | 1 stock holding inside 1 fund's portfolio | 322 |
| `benchmark_indices` | Reference | 1 market index's closing value on 1 day | 8,050 |

**Source of truth:** all data originates from the 10 raw CSVs delivered in Day 1
(`data/raw/01_fund_master.csv` … `10_benchmark_indices.csv`), cleaned by
`clean_nav.py`, `clean_transactions.py`, `clean_performance.py`, and
`clean_others.py` into `data/processed/`, then loaded into SQLite by
`load_to_sqlite.py`.

---

## 2. dim_fund

One row per mutual fund scheme. Source: `01_fund_master.csv` (cleaned, unchanged structurally).

| Column | Type | Business definition | Notes |
|---|---|---|---|
| `amfi_code` | INTEGER (PK) | AMFI scheme code — unique identifier for a fund scheme/plan combination. | Primary key for the whole schema; every fact table references this. |
| `fund_house` | TEXT | Name of the Asset Management Company (AMC) that manages the fund. | 10 distinct fund houses in this dataset. |
| `scheme_name` | TEXT | Full official name of the scheme, including plan type. | e.g. "SBI Bluechip Fund - Regular Plan - Growth" |
| `category` | TEXT | Top-level asset class. | Values: `Equity`, `Debt` |
| `sub_category` | TEXT | SEBI scheme sub-category. | e.g. `Large Cap`, `Small Cap`, `Liquid`, `Gilt`, `ELSS`, `Flexi Cap`, `Index`, etc. |
| `plan` | TEXT | Whether this row is the Regular or Direct plan of the scheme. | Values: `Regular`, `Direct` |
| `launch_date` | TEXT (ISO date) | Date the scheme was launched. | |
| `benchmark` | TEXT | Name of the index this fund is benchmarked against. | e.g. `NIFTY 100 TRI` |
| `expense_ratio_pct` | REAL | Annual expense ratio charged to investors, in percent. | Valid range observed: 0.55–1.64%. |
| `exit_load_pct` | REAL | Exit load charged for early redemption, in percent. | |
| `min_sip_amount` | INTEGER | Minimum SIP investment amount in INR. | |
| `min_lumpsum_amount` | INTEGER | Minimum lumpsum investment amount in INR. | |
| `fund_manager` | TEXT | Name of the fund manager. | |
| `risk_category` | TEXT | SEBI riskometer category. | Values: `Low`, `Moderate`, `Moderately High`, `High`, `Very High`. |
| `sebi_category_code` | TEXT | SEBI's official scheme classification code. | e.g. `EC01` |

---

## 3. dim_date

Standard date dimension. Generated in Python (`load_to_sqlite.py`), not sourced from a CSV — built to span the full range covered by every date column in the other 9 files (2022-01-01 to 2026-05-31, with margin).

| Column | Type | Business definition |
|---|---|---|
| `date_key` | TEXT (PK, ISO date `YYYY-MM-DD`) | The calendar date. Used as the join key from every fact table. |
| `year` | INTEGER | Calendar year. |
| `quarter` | INTEGER | Calendar quarter (1–4). |
| `month` | INTEGER | Calendar month (1–12). |
| `month_name` | TEXT | Full month name, e.g. "January". |
| `day` | INTEGER | Day of month (1–31). |
| `day_of_week` | INTEGER | 0 = Monday … 6 = Sunday. |
| `day_name` | TEXT | Full weekday name, e.g. "Monday". |
| `is_weekend` | INTEGER (0/1) | 1 if Saturday or Sunday. |
| `year_month` | TEXT | `YYYY-MM`, for convenient monthly grouping. |

---

## 4. fact_nav

Daily NAV (Net Asset Value) per fund. Source: `02_nav_history.csv`, cleaned by `clean_nav.py`.

| Column | Type | Business definition | Notes |
|---|---|---|---|
| `amfi_code` | INTEGER (PK part 1, FK → dim_fund) | Fund this NAV belongs to. | |
| `date_key` | TEXT (PK part 2, FK → dim_date) | Date of this NAV value. | |
| `nav` | REAL | Net Asset Value per unit, in INR. | Validated > 0 during cleaning. |
| `is_filled` | INTEGER (0/1) | 1 if this row's NAV was forward-filled from the previous trading day (i.e. a weekend/holiday with no published NAV); 0 if it's an original reported value. | The raw source file only contains business-day rows; cleaning expanded every fund to a full calendar (incl. weekends) and forward-filled the gaps so every fund has exactly one NAV per calendar day. |

**Cleaning applied:** dates parsed to datetime; sorted by `amfi_code` + `date`; duplicate (amfi_code, date) rows removed (keeping the latest); rows with `nav <= 0` dropped; expanded to a full daily calendar per fund with forward-fill for non-trading days.

---

## 5. fact_transactions

One row per investor transaction. Source: `08_investor_transactions.csv`, cleaned by `clean_transactions.py`. Investor demographic fields are kept on this fact table (not split into a separate `dim_investor`) because the source data has no stable investor master file — only an `investor_id` plus per-transaction attributes — so a dimension table would be a deduplicated guess rather than faithful source data.

| Column | Type | Business definition | Notes |
|---|---|---|---|
| `transaction_pk` | INTEGER (PK, autoincrement) | Surrogate key for this transaction row. | Generated on load; not present in source data. |
| `investor_id` | TEXT | Identifier for the investor who made the transaction. | e.g. `INV003054`. 5,000 distinct investors. |
| `date_key` | TEXT (FK → dim_date) | Date the transaction occurred. | |
| `amfi_code` | INTEGER (FK → dim_fund) | Fund the transaction was made into/out of. | |
| `transaction_type` | TEXT | Type of transaction. | Standardised to exactly: `SIP`, `Lumpsum`, `Redemption`. |
| `amount_inr` | REAL | Transaction amount in INR. | Validated > 0 during cleaning. |
| `state` | TEXT | Indian state of the investor. | 12 distinct states. |
| `city` | TEXT | City of the investor. | |
| `city_tier` | TEXT | City tier classification. | Values: `T30` (top 30 cities), `B30` (beyond top 30). |
| `age_group` | TEXT | Investor's age bracket. | Values: `18-25`, `26-35`, `36-45`, `46-55`, `56+`. |
| `gender` | TEXT | Investor's gender. | Values: `Male`, `Female`. |
| `annual_income_lakh` | REAL | Investor's self-reported annual income, in INR lakh. | |
| `payment_mode` | TEXT | Payment channel used. | Values: `UPI`, `Cheque`, `Mandate`, `Net Banking`. |
| `kyc_status` | TEXT | KYC verification status at time of transaction. | Values: `Verified`, `Pending` (any unrecognised value is recoded to `Unknown` during cleaning, none occurred in this dataset). |

**Cleaning applied:** dates parsed to datetime; `transaction_type` standardised to title case and mapped to the 3 canonical values; rows with `amount_inr <= 0` dropped; `kyc_status` validated against the 2 known enum values; exact duplicate rows removed.

---

## 6. fact_performance

One row per fund — a point-in-time trailing-performance snapshot (not a time series). Source: `07_scheme_performance.csv`, cleaned by `clean_performance.py`.

| Column | Type | Business definition | Notes |
|---|---|---|---|
| `amfi_code` | INTEGER (PK, FK → dim_fund) | Fund this snapshot belongs to. | |
| `return_1yr_pct` | REAL | Trailing 1-year return, in percent. | Validated numeric. |
| `return_3yr_pct` | REAL | Trailing 3-year annualised return, in percent. | |
| `return_5yr_pct` | REAL | Trailing 5-year annualised return, in percent. | |
| `benchmark_3yr_pct` | REAL | The fund's benchmark's trailing 3-year return, in percent (for comparison). | |
| `alpha` | REAL | Jensen's alpha — excess return vs. benchmark after adjusting for risk. | |
| `beta` | REAL | Fund's volatility relative to its benchmark (1.0 = moves with benchmark). | |
| `sharpe_ratio` | REAL | Risk-adjusted return measure (return per unit of total risk). | 3 liquid funds flagged as outliers — see anomaly_flags. |
| `sortino_ratio` | REAL | Risk-adjusted return measure using only downside volatility. | |
| `std_dev_ann_pct` | REAL | Annualised standard deviation of returns (volatility), in percent. | |
| `max_drawdown_pct` | REAL | Maximum peak-to-trough decline observed, in percent (negative value). | |
| `aum_crore` | REAL | Assets Under Management for this specific scheme, in INR crore. | |
| `expense_ratio_pct` | REAL | Annual expense ratio, in percent (matches dim_fund's value). | Valid range checked: 0.1%–2.5%. All 40 funds passed. |
| `morningstar_rating` | INTEGER | Morningstar star rating (1–5). | |
| `risk_grade` | TEXT | SEBI riskometer category (matches dim_fund's risk_category). | |
| `anomaly_flags` | TEXT | Semicolon-separated list of data-quality anomalies detected for this row, empty string if none. | Possible flags: `expense_ratio_outside_0.1-2.5pct`, `aum_non_positive`, `positive_max_drawdown`, `negative_std_dev`, `sharpe_ratio_extreme_outlier`, `morningstar_rating_out_of_range`. In this dataset, 3 liquid funds (ICICI Pru Liquid, Kotak Liquid, ABSL Liquid) were flagged for `sharpe_ratio_extreme_outlier` — a real and expected pattern, since liquid funds have near-zero volatility, which inflates the Sharpe ratio formula. Not treated as bad data. |

**Cleaning applied:** all 4 return columns coerced to numeric (none failed); anomaly scan run and flagged (rows kept, not dropped, since reported performance figures are not inherently "wrong" even when unusual); expense ratio checked against the 0.1–2.5% valid range; duplicate `amfi_code` rows removed (kept last).

---

## 7. fact_aum

AUM (Assets Under Management) by fund house over time. Source: `03_aum_by_fund_house.csv`. **Note the grain is fund-house level, not scheme level** — the source file has no `amfi_code`, only `fund_house`, so this table joins to `dim_fund` via the `fund_house` name (not a key relationship) rather than `amfi_code`.

| Column | Type | Business definition | Notes |
|---|---|---|---|
| `fund_house` | TEXT (PK part 1) | Name of the AMC. | Matches `dim_fund.fund_house` exactly (verified, no mismatches). |
| `date_key` | TEXT (PK part 2, FK → dim_date) | Reporting date for this AUM figure. | Quarterly reporting dates in source data. |
| `aum_lakh_crore` | REAL | Total AUM in lakh crore INR (1 lakh crore = 10,000 crore). | |
| `aum_crore` | REAL | Total AUM in crore INR. | Validated > 0. |
| `num_schemes` | INTEGER | Number of schemes the fund house manages as of this date. | Validated > 0. |

---

## 8. monthly_sip_inflows

Industry-wide monthly SIP (Systematic Investment Plan) statistics. Source: `04_monthly_sip_inflows.csv`.

| Column | Type | Business definition | Notes |
|---|---|---|---|
| `month` | TEXT (PK, `YYYY-MM`) | Calendar month. | |
| `sip_inflow_crore` | REAL | Total SIP inflow across the industry that month, in INR crore. | Validated > 0. |
| `active_sip_accounts_crore` | REAL | Number of active SIP accounts, in crore. | |
| `new_sip_accounts_lakh` | REAL | Number of new SIP accounts opened that month, in lakh. | |
| `sip_aum_lakh_crore` | REAL | Total AUM held via SIP, in lakh crore. | |
| `yoy_growth_pct` | REAL | Year-over-year growth in SIP inflow, in percent. | **Null for the first 12 months** (Jan–Dec 2022) by design — there's no prior-year data to compare against yet. This is expected, not a data quality issue. |

---

## 9. category_inflows

Net investor inflows/outflows by fund category, per month. Source: `05_category_inflows.csv`.

| Column | Type | Business definition |
|---|---|---|
| `month` | TEXT (PK part 1, `YYYY-MM`) | Calendar month. |
| `category` | TEXT (PK part 2) | Fund sub-category, e.g. `Large Cap`, `Mid Cap`, `Small Cap`. |
| `net_inflow_crore` | REAL | Net inflow (positive) or outflow (negative) for that category that month, in INR crore. |

---

## 10. industry_folio_count

Industry-wide investor folio (account) counts over time. Source: `06_industry_folio_count.csv`.

| Column | Type | Business definition | Notes |
|---|---|---|---|
| `month` | TEXT (PK, `YYYY-MM`) | Calendar month (quarterly reporting cadence in source data). | |
| `total_folios_crore` | REAL | Total number of investor folios across the industry, in crore. | Validated > 0. |
| `equity_folios_crore` | REAL | Folios in equity schemes, in crore. | |
| `debt_folios_crore` | REAL | Folios in debt schemes, in crore. | |
| `hybrid_folios_crore` | REAL | Folios in hybrid schemes, in crore. | |
| `others_folios_crore` | REAL | Folios in other scheme types, in crore. | |

---

## 11. portfolio_holdings

Individual stock holdings inside each fund's portfolio (a snapshot). Source: `09_portfolio_holdings.csv`.

| Column | Type | Business definition | Notes |
|---|---|---|---|
| `amfi_code` | INTEGER (FK → dim_fund) | Fund this holding belongs to. | FK integrity verified — all codes exist in dim_fund. |
| `stock_symbol` | TEXT | Stock ticker symbol. | e.g. `HDFCBANK`. |
| `stock_name` | TEXT | Full company name. | |
| `sector` | TEXT | Industry sector of the holding. | 14 distinct sectors, e.g. `Banking`, `IT`, `Pharma`. |
| `weight_pct` | REAL | This holding's weight as a percentage of the fund's portfolio. | Validated within (0, 100]. |
| `market_value_cr` | REAL | Market value of this holding, in INR crore. | Validated > 0. |
| `current_price_inr` | REAL | Current market price of the stock, in INR. | Validated > 0. |
| `portfolio_date` | TEXT (ISO date) | Date this holdings snapshot was taken. | Single snapshot date in this dataset: 2025-12-31. |

---

## 12. benchmark_indices

Daily closing values for market benchmark indices. Source: `10_benchmark_indices.csv`.

| Column | Type | Business definition | Notes |
|---|---|---|---|
| `date_key` | TEXT (PK part 1, FK → dim_date) | Date of this closing value. | |
| `index_name` | TEXT (PK part 2) | Name of the benchmark index. | 7 indices: `NIFTY50`, `NIFTY100`, `NIFTY_MIDCAP150`, `BSE_SMALLCAP`, `NIFTY500`, `CRISIL_LIQUID`, `CRISIL_GILT`. |
| `close_value` | REAL | Closing value of the index on this date. | Validated > 0. |

---

## 13. Known data quality notes (carried over from cleaning)

- **fact_nav**: ~22% of rows (`is_filled = 1`) are forward-filled, not originally reported — always check this flag before treating a NAV value as an actual market quote vs. a carried-forward weekend/holiday value.
- **monthly_sip_inflows**: `yoy_growth_pct` is null for the first 12 calendar months in the dataset by design (no prior year to compare).
- **fact_performance**: 3 liquid funds carry a `sharpe_ratio_extreme_outlier` anomaly flag — expected behavior for low-volatility liquid funds, not a data error.
- **fact_aum** vs **dim_fund**: joins on `fund_house` name string, not a surrogate key — all 10 fund house names were verified to match exactly between the two source files, but this remains a soft join (no FK constraint enforced in SQLite for this relationship).

---

## 14. File-to-table source map

| Raw CSV (Day 1) | Cleaned CSV (Day 2) | SQLite table(s) | Cleaning script |
|---|---|---|---|
| `01_fund_master.csv` | `data/processed/01_fund_master.csv` | `dim_fund` | `clean_others.py` |
| `02_nav_history.csv` | `data/processed/02_nav_history.csv` | `fact_nav` | `clean_nav.py` |
| `03_aum_by_fund_house.csv` | `data/processed/03_aum_by_fund_house.csv` | `fact_aum` | `clean_others.py` |
| `04_monthly_sip_inflows.csv` | `data/processed/04_monthly_sip_inflows.csv` | `monthly_sip_inflows` | `clean_others.py` |
| `05_category_inflows.csv` | `data/processed/05_category_inflows.csv` | `category_inflows` | `clean_others.py` |
| `06_industry_folio_count.csv` | `data/processed/06_industry_folio_count.csv` | `industry_folio_count` | `clean_others.py` |
| `07_scheme_performance.csv` | `data/processed/07_scheme_performance.csv` | `fact_performance` | `clean_performance.py` |
| `08_investor_transactions.csv` | `data/processed/08_investor_transactions.csv` | `fact_transactions` | `clean_transactions.py` |
| `09_portfolio_holdings.csv` | `data/processed/09_portfolio_holdings.csv` | `portfolio_holdings` | `clean_others.py` |
| `10_benchmark_indices.csv` | `data/processed/10_benchmark_indices.csv` | `benchmark_indices` | `clean_others.py` |
| *(generated)* | — | `dim_date` | `load_to_sqlite.py` |