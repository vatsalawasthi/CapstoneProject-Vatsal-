-- ===========================================================================
-- schema.sql
-- ---------------------------------------------------------------------------
-- Day 2 Task: SQLite star schema for the Bluestock Mutual Fund capstone.
--
-- Design notes:
--   - dim_fund        : one row per scheme (amfi_code), from fund_master.
--                       Includes the latest known performance/risk snapshot
--                       columns are kept OUT of this table on purpose --
--                       performance is time-varying-ish (re-measured), so it
--                       lives in fact_performance, not as a fund attribute.
--   - dim_date        : standard date dimension, one row per calendar day,
--                       spanning the full range seen across all fact tables
--                       (2022-01-01 -> 2026-05-31). Built in Python
--                       (build_schema.py) since SQLite has no native
--                       date-series generator before 3.39's generate_series.
--   - fact_nav         : daily NAV per fund (grain: 1 row per amfi_code+date).
--                       Sourced from cleaned 02_nav_history.csv (post
--                       forward-fill, so it has one row per fund per
--                       calendar day, not just trading days).
--   - fact_transactions: one row per investor transaction (grain: 1 row per
--                       transaction). Investor demographic attributes
--                       (state/city/age_group/gender/etc.) are denormalised
--                       onto this fact table rather than split into a
--                       separate dim_investor, since the source data has no
--                       stable investor master file (only an investor_id +
--                       per-transaction attributes) -- a "dim_investor"
--                       would just be a deduplicated guess. This keeps the
--                       data faithful to source.
--   - fact_performance : one row per fund (grain: 1 row per amfi_code) --
--                       this is a point-in-time performance snapshot per
--                       scheme, not a time series, since the source file
--                       (07_scheme_performance.csv) has exactly one row
--                       per amfi_code with trailing 1Y/3Y/5Y returns.
--   - fact_aum         : AUM by fund house over time (grain: 1 row per
--                       fund_house + date). Note this is at FUND HOUSE
--                       grain, not scheme grain (source file
--                       03_aum_by_fund_house.csv has no amfi_code), so it
--                       joins to dim_fund via fund_house name, not a key.
--
--   Three supporting tables (not part of the star, but useful reference
--   data the brief's other CSVs map to) are also created:
--   monthly_sip_inflows, category_inflows, industry_folio_count,
--   portfolio_holdings, benchmark_indices.
-- ===========================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- DIMENSION: dim_fund
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_fund;
CREATE TABLE dim_fund (
    amfi_code           INTEGER PRIMARY KEY,
    fund_house          TEXT NOT NULL,
    scheme_name         TEXT NOT NULL,
    category            TEXT NOT NULL,        -- Equity / Debt
    sub_category        TEXT NOT NULL,        -- Large Cap, Liquid, Gilt, etc.
    plan                TEXT NOT NULL,        -- Regular / Direct
    launch_date         TEXT,                 -- ISO date string (YYYY-MM-DD)
    benchmark           TEXT,
    expense_ratio_pct   REAL,
    exit_load_pct       REAL,
    min_sip_amount      INTEGER,
    min_lumpsum_amount  INTEGER,
    fund_manager        TEXT,
    risk_category       TEXT,
    sebi_category_code  TEXT
);

-- ---------------------------------------------------------------------------
-- DIMENSION: dim_date
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date (
    date_key      TEXT PRIMARY KEY,   -- ISO date string (YYYY-MM-DD), used as FK
    year          INTEGER NOT NULL,
    quarter       INTEGER NOT NULL,
    month         INTEGER NOT NULL,
    month_name    TEXT NOT NULL,
    day           INTEGER NOT NULL,
    day_of_week   INTEGER NOT NULL,    -- 0=Monday ... 6=Sunday
    day_name      TEXT NOT NULL,
    is_weekend    INTEGER NOT NULL,    -- 0/1
    year_month    TEXT NOT NULL        -- 'YYYY-MM', handy for monthly grouping
);

-- ---------------------------------------------------------------------------
-- FACT: fact_nav  (grain: amfi_code + date)
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_nav;
CREATE TABLE fact_nav (
    amfi_code   INTEGER NOT NULL,
    date_key    TEXT NOT NULL,
    nav         REAL NOT NULL,
    is_filled   INTEGER NOT NULL,   -- 1 if forward-filled (non-trading day)
    PRIMARY KEY (amfi_code, date_key),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_key)  REFERENCES dim_date(date_key)
);

-- ---------------------------------------------------------------------------
-- FACT: fact_transactions  (grain: 1 row per transaction)
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_transactions;
CREATE TABLE fact_transactions (
    transaction_pk      INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id          TEXT NOT NULL,
    date_key             TEXT NOT NULL,
    amfi_code            INTEGER NOT NULL,
    transaction_type     TEXT NOT NULL,   -- SIP / Lumpsum / Redemption
    amount_inr           REAL NOT NULL,
    state                TEXT,
    city                 TEXT,
    city_tier            TEXT,
    age_group            TEXT,
    gender               TEXT,
    annual_income_lakh   REAL,
    payment_mode         TEXT,
    kyc_status           TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_key)  REFERENCES dim_date(date_key)
);

-- ---------------------------------------------------------------------------
-- FACT: fact_performance  (grain: 1 row per amfi_code -- snapshot)
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_performance;
CREATE TABLE fact_performance (
    amfi_code           INTEGER PRIMARY KEY,
    return_1yr_pct      REAL,
    return_3yr_pct      REAL,
    return_5yr_pct      REAL,
    benchmark_3yr_pct   REAL,
    alpha               REAL,
    beta                REAL,
    sharpe_ratio        REAL,
    sortino_ratio       REAL,
    std_dev_ann_pct     REAL,
    max_drawdown_pct    REAL,
    aum_crore           REAL,
    expense_ratio_pct   REAL,
    morningstar_rating  INTEGER,
    risk_grade          TEXT,
    anomaly_flags       TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- ---------------------------------------------------------------------------
-- FACT: fact_aum  (grain: fund_house + date; fund-house level, not scheme level)
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_aum;
CREATE TABLE fact_aum (
    fund_house       TEXT NOT NULL,
    date_key         TEXT NOT NULL,
    aum_lakh_crore   REAL,
    aum_crore        REAL NOT NULL,
    num_schemes      INTEGER,
    PRIMARY KEY (fund_house, date_key),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

-- ---------------------------------------------------------------------------
-- SUPPORTING REFERENCE TABLES (not part of the star schema proper, but
-- loaded from the remaining cleaned CSVs so all 10 datasets live in the DB)
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS monthly_sip_inflows;
CREATE TABLE monthly_sip_inflows (
    month                       TEXT PRIMARY KEY,  -- 'YYYY-MM'
    sip_inflow_crore            REAL NOT NULL,
    active_sip_accounts_crore   REAL,
    new_sip_accounts_lakh       REAL,
    sip_aum_lakh_crore          REAL,
    yoy_growth_pct              REAL
);

DROP TABLE IF EXISTS category_inflows;
CREATE TABLE category_inflows (
    month             TEXT NOT NULL,
    category          TEXT NOT NULL,
    net_inflow_crore  REAL,
    PRIMARY KEY (month, category)
);

DROP TABLE IF EXISTS industry_folio_count;
CREATE TABLE industry_folio_count (
    month                  TEXT PRIMARY KEY,
    total_folios_crore     REAL,
    equity_folios_crore    REAL,
    debt_folios_crore      REAL,
    hybrid_folios_crore    REAL,
    others_folios_crore    REAL
);

DROP TABLE IF EXISTS portfolio_holdings;
CREATE TABLE portfolio_holdings (
    amfi_code           INTEGER NOT NULL,
    stock_symbol         TEXT NOT NULL,
    stock_name           TEXT,
    sector               TEXT,
    weight_pct           REAL,
    market_value_cr      REAL,
    current_price_inr    REAL,
    portfolio_date        TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

DROP TABLE IF EXISTS benchmark_indices;
CREATE TABLE benchmark_indices (
    date_key      TEXT NOT NULL,
    index_name    TEXT NOT NULL,
    close_value   REAL NOT NULL,
    PRIMARY KEY (date_key, index_name),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);
