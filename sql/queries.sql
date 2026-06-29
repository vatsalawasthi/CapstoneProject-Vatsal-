-- ===========================================================================
-- queries.sql
-- ---------------------------------------------------------------------------
-- Day 2 Task: 10 analytical SQL queries against bluestock_mf.db
--
-- Queries 1-5 are the specific ones requested in the task brief.
-- Queries 6-10 are 5 additional queries chosen to exercise different parts
-- of the star schema (performance, transactions, holdings, inflows, KYC).
--
-- Run any of these with:
--   sqlite3 bluestock_mf.db < sql/queries.sql
-- or open bluestock_mf.db in DB Browser for SQLite / VS Code SQLite extension
-- and run them individually.
-- ===========================================================================


-- ---------------------------------------------------------------------------
-- Q1. Top 5 funds by AUM
-- ---------------------------------------------------------------------------
SELECT
    f.scheme_name,
    f.fund_house,
    p.aum_crore
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;


-- ---------------------------------------------------------------------------
-- Q2. Average NAV per month (across all funds, overall market trend)
-- ---------------------------------------------------------------------------
SELECT
    d.year_month,
    ROUND(AVG(n.nav), 2) AS avg_nav
FROM fact_nav n
JOIN dim_date d ON d.date_key = n.date_key
GROUP BY d.year_month
ORDER BY d.year_month;


-- ---------------------------------------------------------------------------
-- Q3. SIP YoY growth (monthly SIP inflows + reported YoY growth %)
-- ---------------------------------------------------------------------------
SELECT
    month,
    sip_inflow_crore,
    yoy_growth_pct
FROM monthly_sip_inflows
ORDER BY month;


-- ---------------------------------------------------------------------------
-- Q4. Transactions by state (volume + value, descending)
-- ---------------------------------------------------------------------------
SELECT
    state,
    COUNT(*) AS num_transactions,
    ROUND(SUM(amount_inr), 0) AS total_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY num_transactions DESC;


-- ---------------------------------------------------------------------------
-- Q5. Funds with expense_ratio < 1%  (cheapest funds for cost-conscious investors)
-- ---------------------------------------------------------------------------
SELECT
    f.scheme_name,
    f.fund_house,
    f.expense_ratio_pct
FROM dim_fund f
WHERE f.expense_ratio_pct < 1.0
ORDER BY f.expense_ratio_pct;


-- ===========================================================================
-- 5 additional queries of choice
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- Q6. Top 5 funds by trailing 3-year return
-- ---------------------------------------------------------------------------
SELECT
    f.scheme_name,
    f.fund_house,
    p.return_3yr_pct
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
ORDER BY p.return_3yr_pct DESC
LIMIT 5;


-- ---------------------------------------------------------------------------
-- Q7. SIP vs Lumpsum vs Redemption breakdown -- transaction count, total
--     value, and average ticket size per type
-- ---------------------------------------------------------------------------
SELECT
    transaction_type,
    COUNT(*) AS num_txns,
    ROUND(SUM(amount_inr), 0) AS total_inr,
    ROUND(AVG(amount_inr), 0) AS avg_inr
FROM fact_transactions
GROUP BY transaction_type
ORDER BY total_inr DESC;


-- ---------------------------------------------------------------------------
-- Q8. Sector exposure across all fund portfolio holdings (by market value),
--     top 5 sectors -- a portfolio concentration / industry exposure view
-- ---------------------------------------------------------------------------
SELECT
    sector,
    ROUND(SUM(market_value_cr), 2) AS total_market_value_cr,
    COUNT(*) AS num_holdings
FROM portfolio_holdings
GROUP BY sector
ORDER BY total_market_value_cr DESC
LIMIT 5;


-- ---------------------------------------------------------------------------
-- Q9. Monthly net category inflows: Large Cap vs Small Cap (most recent 6
--     data points) -- shows relative investor appetite for risk over time
-- ---------------------------------------------------------------------------
SELECT
    month,
    category,
    net_inflow_crore
FROM category_inflows
WHERE category IN ('Large Cap', 'Small Cap')
ORDER BY month DESC, category
LIMIT 6;


-- ---------------------------------------------------------------------------
-- Q10. KYC-pending transactions by payment mode -- a compliance/risk view
--      of which payment channels carry the most unverified-investor volume
-- ---------------------------------------------------------------------------
SELECT
    payment_mode,
    COUNT(*) AS pending_kyc_txns,
    ROUND(SUM(amount_inr), 0) AS total_inr
FROM fact_transactions
WHERE kyc_status = 'Pending'
GROUP BY payment_mode
ORDER BY pending_kyc_txns DESC;