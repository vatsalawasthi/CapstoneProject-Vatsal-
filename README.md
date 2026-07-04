# Bluestock Mutual Fund Analytics — Capstone Project

**Student:** Vatsal Awasthi
**Organisation:** Bluestock Fintech Internship
**Period:** June–July 2026
**Repository:** [github.com/vatsalawasthi/CapstoneProject-Vatsal-](https://github.com/vatsalawasthi/CapstoneProject-Vatsal-)

---

## Project Overview

End-to-end data analytics pipeline for a mutual fund dataset covering **40 schemes across 10 fund houses**. The project progresses from raw CSV ingestion through data cleaning, exploratory analysis, quantitative performance metrics, interactive Power BI dashboard, and advanced risk analytics — all built on real mutual fund data spanning January 2022 to May 2026.

---

## Project Structure

```
CapstoneProject-Vatsal/
├── data/
│   ├── raw/                        ← original 10 CSV datasets
│   ├── processed/                  ← cleaned CSVs (output of Day 2)
│   └── db/
│       └── bluestock_mf.db         ← SQLite star schema database
├── notebooks/
│   ├── 01_data_ingestion.ipynb     ← Day 1: ETL and profiling
│   ├── 02_data_cleaning.ipynb      ← Day 2: Cleaning and SQL
│   ├── 03_eda_analysis.ipynb       ← Day 3: Exploratory analysis
│   ├── 04_performance_analytics.ipynb  ← Day 4: Performance metrics
│   └── 05_advanced_analytics.ipynb ← Day 6: Risk and advanced analytics
├── scripts/
│   ├── etl_pipeline.py             ← loads + profiles all 10 CSVs
│   ├── live_nav_fetch.py           ← fetches live NAV from mfapi.in
│   ├── compute_metrics.py          ← computes CAGR, Sharpe, Sortino, etc.
│   └── recommender.py              ← fund recommender by risk appetite
├── sql/
│   ├── schema.sql                  ← SQLite star schema DDL
│   └── queries.sql                 ← 10 analytical SQL queries
├── dashboard/
│   ├── bluestock_mf_dashboard.pbix ← Power BI dashboard (4 pages)
│   ├── Dashboard.pdf               ← PDF export
│   └── Page1–4_*.png               ← PNG screenshots of each page
├── reports/
│   ├── Final_Report.docx           ← comprehensive report (all 6 days)
│   ├── Presentation.pptx           ← 16-slide project presentation
│   ├── charts/                     ← all exported chart PNGs (01–16)
│   └── at_risk_sip_investors.csv   ← SIP continuity analysis output
├── alpha_beta.csv                  ← Alpha, Beta, R² for all 40 funds
├── fund_scorecard.csv              ← 0–100 composite scorecard
├── var_cvar_report.csv             ← VaR and CVaR for all 40 funds
├── data_dictionary.md              ← column-level documentation for all 11 DB tables
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Dataset

| File | Description | Rows |
|---|---|---|
| 01_fund_master.csv | 40 fund schemes, metadata | 40 |
| 02_nav_history.csv | Daily NAV per fund | 46,000 |
| 03_aum_by_fund_house.csv | AUM by AMC over time | 90 |
| 04_monthly_sip_inflows.csv | Industry SIP inflows | 48 |
| 05_category_inflows.csv | Net inflows by category | 144 |
| 06_industry_folio_count.csv | Industry folio count | 21 |
| 07_scheme_performance.csv | Performance snapshot | 40 |
| 08_investor_transactions.csv | Investor transactions | 32,778 |
| 09_portfolio_holdings.csv | Equity fund holdings | 322 |
| 10_benchmark_indices.csv | 7 benchmark indices | 8,050 |

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/vatsalawasthi/CapstoneProject-Vatsal-.git
cd CapstoneProject-Vatsal-
```

### 2. Create virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add raw datasets

Copy the 10 provided CSV files into `data/raw/`.

---

## Running the Project

### Day 1 — Data Ingestion

```bash
python scripts/etl_pipeline.py      # profile all 10 CSVs, validate AMFI codes
python scripts/live_nav_fetch.py    # fetch live NAV from mfapi.in
```

### Day 2 — Data Cleaning + SQL

Open and run all cells in `notebooks/02_data_cleaning.ipynb`.
This cleans all 10 CSVs and loads them into `data/db/bluestock_mf.db`.

### Day 3 — EDA

```bash
jupyter notebook notebooks/03_eda_analysis.ipynb
```
Or open in VS Code with the Jupyter extension.

### Day 4 — Performance Analytics

```bash
jupyter notebook notebooks/04_performance_analytics.ipynb
```
Outputs: `fund_scorecard.csv`, `alpha_beta.csv`, benchmark comparison chart.

### Day 5 — Power BI Dashboard

Open `dashboard/bluestock_mf_dashboard.pbix` in Power BI Desktop.
All data connections point to `data/processed/` — refresh if needed.

### Day 6 — Advanced Analytics

```bash
jupyter notebook notebooks/05_advanced_analytics.ipynb
```
Outputs: `var_cvar_report.csv`, rolling Sharpe chart, SIP continuity analysis.

### Fund Recommender (standalone)

```bash
python scripts/recommender.py Low
python scripts/recommender.py Moderate
python scripts/recommender.py High
```

---

## Day-wise Summary

### Day 1 — Project Setup + Data Ingestion
- Loaded and profiled all 10 CSV datasets
- Validated AMFI code consistency between fund_master and nav_history
- Fetched live NAV from mfapi.in for 6 key schemes
- **Finding:** All 46,000 NAV rows are weekday-only; all AMFI codes consistent

### Day 2 — Data Cleaning + SQL Database Design
- Cleaned nav_history (forward-filled weekends → 64,320 rows), investor_transactions, scheme_performance
- Designed and loaded SQLite star schema: 2 dimensions, 4 facts, 5 reference tables = 11 tables total
- Wrote 10 analytical SQL queries
- **Finding:** 3 liquid funds flagged for extreme Sharpe ratio (expected behavior, rows retained)

### Day 3 — Exploratory Data Analysis
- Built 9 chart sections (15+ charts) using Plotly, Seaborn, and Matplotlib
- Documented 10 key findings in Jupyter Markdown cells
- **Finding:** NAV growth is smooth at ~12-14%/year; SIP inflows grew 2.7× to ₹31,002 Cr

### Day 4 — Fund Performance Analytics
- Computed daily returns, CAGR (1yr/3yr), Sharpe, Sortino, Alpha/Beta, max drawdown
- Built weighted 0–100 Fund Scorecard across all 40 funds
- **Finding:** Alpha/Beta regressions have R² < 1% — NAV series are not market-driven

### Day 5 — Power BI Dashboard
- 4-page interactive dashboard: Industry Overview, Fund Performance, Investor Analytics, SIP & Market Trends
- Connected to all cleaned CSVs; DAX measures for KPI cards and dual-axis charts
- **Finding:** Task brief's Total AUM (₹81L Cr) did not match actual data (₹62.74L Cr); dashboard shows real values

### Day 6 — Advanced Analytics + Risk Metrics
- Historical VaR(95%) and CVaR for all 40 funds
- Rolling 90-day Sharpe for 5 key funds
- Investor cohort analysis, SIP continuity analysis (at-risk flagging)
- Fund recommender by risk appetite, Sector HHI concentration
- **Finding:** 73.5% of equity funds show Low HHI — well-diversified portfolios

---

## Key Results

| Metric | Value |
|---|---|
| Total funds analysed | 40 schemes across 10 AMCs |
| NAV history | Jan 2022 – May 2026 (~4.4 years) |
| Top fund by AUM | Mirae Asset Emerging Bluechip (₹49,046 Cr) |
| Top fund by 3yr CAGR | Axis Midcap (35.1%) |
| Industry AUM leader | SBI Mutual Fund (₹12.5L Cr by 2025) |
| SIP inflow peak | ₹31,002 Cr (December 2025) |
| Folio count growth | 13.26 Cr → 26.12 Cr (+97% in 4 years) |
| Top sector exposure | Banking (₹62,840 Cr, 19.3% of equity holdings) |
| Cheapest fund | Nippon India Gilt Securities (0.55% expense ratio) |

---

## Technology Stack

- **Python 3.14** — pandas, numpy, scipy, matplotlib, seaborn, plotly, sqlalchemy
- **SQLite** — star schema with 11 tables
- **Jupyter Notebooks** — 5 analytical notebooks
- **Power BI Desktop** — 4-page interactive dashboard
- **GitHub** — version control, 7 commits

---

## Important Data Notes

1. **Forward-filled NAV rows:** `02_nav_history.csv` in `data/processed/` contains calendar-expanded rows (including weekends) flagged with `is_filled = True`. Always filter to `is_filled == False` before computing return-based metrics.

2. **NAV history span:** Data covers ~4.4 years (not 5), so "5yr CAGR" in `04_performance_analytics.ipynb` uses the pre-reported figure from `scheme_performance.csv` rather than recomputing from insufficient NAV history.

3. **NAV correlation characteristic:** Daily return correlations between funds are near zero — including between Regular and Direct plans of the same fund. This indicates the NAV series were generated independently rather than tracking a shared market. Alpha/Beta and tracking error figures reflect this and should not be read as genuine fund-manager skill signals.

---

## Deliverables Checklist

- [x] `scripts/etl_pipeline.py` — ETL pipeline
- [x] `scripts/live_nav_fetch.py` — live NAV fetch
- [x] `scripts/recommender.py` — fund recommender
- [x] `notebooks/01_data_ingestion.ipynb` — Day 1 notebook
- [x] `notebooks/02_data_cleaning.ipynb` — Day 2 notebook
- [x] `notebooks/03_eda_analysis.ipynb` — EDA notebook (15+ charts)
- [x] `notebooks/04_performance_analytics.ipynb` — performance analytics
- [x] `notebooks/05_advanced_analytics.ipynb` — advanced risk metrics
- [x] `data/db/bluestock_mf.db` — SQLite database
- [x] `sql/schema.sql` — star schema DDL
- [x] `sql/queries.sql` — 10 analytical queries
- [x] `data_dictionary.md` — column-level documentation
- [x] `fund_scorecard.csv` — composite fund scorecard
- [x] `alpha_beta.csv` — Alpha/Beta table
- [x] `var_cvar_report.csv` — VaR/CVaR report
- [x] `dashboard/bluestock_mf_dashboard.pbix` — Power BI dashboard
- [x] `dashboard/Dashboard.pdf` — PDF export
- [x] `reports/Final_Report.docx` — comprehensive final report
- [x] `reports/Presentation.pptx` — project presentation
- [x] GitHub repository with all commits