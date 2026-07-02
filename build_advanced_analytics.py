"""
build_advanced_analytics.py
-----------------------------
Generates notebooks/Advanced_Analytics.ipynb for Day 6
(Advanced Analytics + Risk Metrics).

Deliverables produced when the notebook runs:
  - var_cvar_report.csv      (project root)
  - recommender.py           (project root)
  - reports/charts/rolling_sharpe_chart.png
  - reports/charts/12_var_cvar_bar.png
  - reports/charts/13_rolling_sharpe.png
  - reports/charts/14_hhi_concentration.png
  - reports/charts/15_sip_continuity.png

All metrics computed from real cleaned CSVs in data/processed/.

Run:
    python build_advanced_analytics.py
"""

import json
from pathlib import Path

NB_PATH = Path(__file__).resolve().parent / "notebooks" / "Advanced_Analytics.ipynb"

cells = []

def md(text):
    cells.append({"cell_type": "markdown", "metadata": {},
                  "source": text.splitlines(keepends=True)})

def code(text):
    cells.append({"cell_type": "code", "execution_count": None,
                  "metadata": {}, "outputs": [],
                  "source": text.splitlines(keepends=True)})

# ===========================================================================
# Title + setup
# ===========================================================================

md("""# Day 6 — Advanced Analytics + Risk Metrics
## Bluestock Mutual Fund Capstone

**Sections:**
1. Historical VaR (95%) and CVaR for all 40 funds
2. Rolling 90-day Sharpe Ratio for 5 key funds
3. Investor cohort analysis (by first transaction year)
4. SIP continuity analysis — at-risk investors
5. Simple fund recommender (by risk appetite)
6. Sector HHI concentration across all equity funds
7. Key findings summary
""")

code("""# Setup
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)

DATA_DIR = Path("..") / "data" / "processed"
CHART_DIR = Path("..") / "reports" / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

RF_DAILY = 0.065 / 252
TRADING_DAYS = 252

fund_master  = pd.read_csv(DATA_DIR / "01_fund_master.csv")
nav_history  = pd.read_csv(DATA_DIR / "02_nav_history.csv", parse_dates=["date"])
transactions = pd.read_csv(DATA_DIR / "08_investor_transactions.csv",
                           parse_dates=["transaction_date"])
holdings     = pd.read_csv(DATA_DIR / "09_portfolio_holdings.csv")

# Always use trading-day-only NAV (same rule as Day 4)
nav_orig = nav_history[~nav_history["is_filled"]].copy().sort_values(["amfi_code", "date"])

print("Datasets loaded:")
print(f"  fund_master:  {fund_master.shape}")
print(f"  nav_history:  {nav_history.shape} (full calendar)")
print(f"  nav_orig:     {nav_orig.shape} (trading days only)")
print(f"  transactions: {transactions.shape}")
print(f"  holdings:     {holdings.shape}")
""")

# ===========================================================================
# 1. VaR / CVaR
# ===========================================================================

md("""---
## 1. Historical VaR (95%) and CVaR — All 40 Funds

**VaR (95%)** = 5th percentile of the daily return distribution.
Interpretation: on 95% of trading days, the fund's loss will not exceed
this value. Computed using the historical simulation method (no
distribution assumption).

**CVaR (95%)** = mean of all returns that fall below the VaR threshold.
Also called Expected Shortfall — answers "when things do go bad, how bad
on average?" CVaR is always more negative than VaR.

Both metrics use only original trading-day NAV rows (is_filled == False),
consistent with Day 4's methodology.""")

code("""var_rows = []
for code_, grp in nav_orig.groupby("amfi_code"):
    ret = grp.sort_values("date")["nav"].pct_change().dropna()
    var95 = np.percentile(ret, 5)
    cvar95 = ret[ret <= var95].mean()
    var_rows.append({
        "amfi_code": code_,
        "var_95_pct": round(var95 * 100, 4),
        "cvar_95_pct": round(cvar95 * 100, 4),
        "n_returns": len(ret),
    })

var_df = pd.DataFrame(var_rows).merge(
    fund_master[["amfi_code", "scheme_name", "fund_house", "category", "risk_category"]],
    on="amfi_code"
)
var_df = var_df.sort_values("var_95_pct").reset_index(drop=True)

print("VaR / CVaR Report (all 40 funds, sorted worst to best VaR):")
print(var_df[["scheme_name", "category", "risk_category",
              "var_95_pct", "cvar_95_pct"]].to_string(index=False))

# Save deliverable
var_df.to_csv("../var_cvar_report.csv", index=False)
print(f"\\nSaved var_cvar_report.csv ({len(var_df)} rows)")
""")

code("""# Bar chart: VaR and CVaR side by side for all 40 funds
short_names = var_df["scheme_name"].str.replace(" - Regular - Growth", ""
    ).str.replace(" - Regular Plan - Growth", ""
    ).str.replace(" Fund", "")

fig, ax = plt.subplots(figsize=(14, 10))
x = np.arange(len(var_df))
width = 0.4
bars1 = ax.barh(x - width/2, var_df["var_95_pct"], width,
                label="VaR (95%)", color="#C0392B", alpha=0.85)
bars2 = ax.barh(x + width/2, var_df["cvar_95_pct"], width,
                label="CVaR (95%)", color="#922B21", alpha=0.85)
ax.set_yticks(x)
ax.set_yticklabels(short_names, fontsize=8)
ax.set_xlabel("Daily Loss (%)")
ax.set_title("Historical VaR(95%) and CVaR(95%) — All 40 Funds\\n"
             "(more negative = riskier; small-cap funds worst as expected)", fontsize=13)
ax.axvline(0, color="black", linewidth=0.8)
ax.legend()
plt.tight_layout()
plt.savefig(CHART_DIR / "12_var_cvar_bar.png", dpi=150, bbox_inches="tight")
plt.show()
print("Chart saved: 12_var_cvar_bar.png")

print("\\nTop 5 highest-risk funds (worst VaR):")
print(var_df.head(5)[["scheme_name", "var_95_pct", "cvar_95_pct",
                        "risk_category"]].to_string(index=False))
print("\\nTop 5 lowest-risk funds (best VaR):")
print(var_df.tail(5)[["scheme_name", "var_95_pct", "cvar_95_pct",
                        "risk_category"]].to_string(index=False))
""")

# ===========================================================================
# 2. Rolling 90-day Sharpe
# ===========================================================================

md("""---
## 2. Rolling 90-Day Sharpe Ratio — 5 Key Funds

Rolling Sharpe = returns.rolling(90).mean() / returns.rolling(90).std()
× √252, using Rf = 6.5% daily.

5 funds selected to represent different categories: one large cap, one
mid cap, one small cap, one liquid (debt), one gilt — so the chart shows
how rolling risk-adjusted performance differs across fund types.""")

code("""# 5 representative funds
KEY_FUNDS = {
    119551: "SBI Bluechip (Large Cap)",
    119094: "Axis Midcap (Mid Cap)",
    119598: "SBI Small Cap (Small Cap)",
    120507: "ICICI Pru Liquid (Liquid)",
    119120: "SBI Magnum Gilt (Gilt)",
}

fig, ax = plt.subplots(figsize=(14, 7))
colors = ["#2E75B6", "#E67E22", "#27AE60", "#8E44AD", "#C0392B"]

for (code_, label), color in zip(KEY_FUNDS.items(), colors):
    grp = nav_orig[nav_orig.amfi_code == code_].sort_values("date").set_index("date")["nav"]
    ret = grp.pct_change().dropna()
    rolling_sharpe = (
        (ret.rolling(90).mean() - RF_DAILY) /
        ret.rolling(90).std() *
        np.sqrt(TRADING_DAYS)
    )
    ax.plot(rolling_sharpe.index, rolling_sharpe.values, label=label,
            color=color, linewidth=1.5)

ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
ax.set_title("Rolling 90-Day Sharpe Ratio — 5 Key Funds (Rf = 6.5%)", fontsize=14)
ax.set_xlabel("Date")
ax.set_ylabel("Rolling Sharpe Ratio")
ax.legend(loc="upper left")
plt.tight_layout()
plt.savefig(CHART_DIR / "13_rolling_sharpe.png", dpi=150, bbox_inches="tight")
# Also save to project root as per deliverable spec
plt.savefig("../rolling_sharpe_chart.png", dpi=150, bbox_inches="tight")
plt.show()
print("Charts saved: 13_rolling_sharpe.png and rolling_sharpe_chart.png")
""")

# ===========================================================================
# 3. Investor cohort analysis
# ===========================================================================

md("""---
## 3. Investor Cohort Analysis

Group investors by their **first transaction year** (i.e. the year they
first appeared in the dataset). For each cohort, compute:
- Number of unique investors
- Average SIP amount
- Total amount invested (all transaction types)
- Top fund preference (most frequently chosen fund by that cohort)

**Data note:** transaction data spans 2024–2025 only, so cohorts are
limited to those two years. 2024 cohort is much larger (4,456 investors
vs 197 in 2025), which makes sense — 2024 investors have had more time
to accumulate transactions in this dataset.""")

code("""sip_tx = transactions[transactions["transaction_type"] == "SIP"].copy()

# Assign cohort = year of investor's first-ever transaction (any type)
transactions["cohort"] = transactions.groupby("investor_id")[
    "transaction_date"].transform("min").dt.year
sip_tx["cohort"] = sip_tx["investor_id"].map(
    transactions.drop_duplicates("investor_id").set_index("investor_id")["cohort"])

cohort_df = sip_tx.groupby("cohort").agg(
    num_investors=("investor_id", "nunique"),
    avg_sip_amount=("amount_inr", "mean"),
    total_sip_invested=("amount_inr", "sum"),
    top_fund_code=("amfi_code", lambda x: x.value_counts().index[0]),
).reset_index()

cohort_df["avg_sip_amount"] = cohort_df["avg_sip_amount"].round(0)
cohort_df["total_sip_invested_cr"] = (cohort_df["total_sip_invested"] / 1e7).round(2)
cohort_df = cohort_df.merge(
    fund_master[["amfi_code", "scheme_name"]].rename(
        columns={"amfi_code": "top_fund_code", "scheme_name": "top_fund_name"}),
    on="top_fund_code", how="left"
)

print("Investor Cohort Analysis:")
print(cohort_df[["cohort", "num_investors", "avg_sip_amount",
                  "total_sip_invested_cr", "top_fund_name"]].to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].bar(cohort_df["cohort"].astype(str), cohort_df["num_investors"],
            color=["#2E75B6", "#E67E22"])
axes[0].set_title("Number of Investors by Cohort")
axes[0].set_xlabel("First Transaction Year")
axes[0].set_ylabel("Unique Investors")
for i, v in enumerate(cohort_df["num_investors"]):
    axes[0].text(i, v + 20, str(v), ha="center", fontweight="bold")

axes[1].bar(cohort_df["cohort"].astype(str), cohort_df["avg_sip_amount"],
            color=["#27AE60", "#8E44AD"])
axes[1].set_title("Avg SIP Amount by Cohort (₹)")
axes[1].set_xlabel("First Transaction Year")
axes[1].set_ylabel("Avg SIP Amount (₹)")
for i, v in enumerate(cohort_df["avg_sip_amount"]):
    axes[1].text(i, v + 50, f"₹{v:,.0f}", ha="center", fontweight="bold")

plt.tight_layout()
plt.savefig(CHART_DIR / "14_investor_cohort.png", dpi=150, bbox_inches="tight")
plt.show()
print("Chart saved: 14_investor_cohort.png")
""")

# ===========================================================================
# 4. SIP continuity analysis
# ===========================================================================

md("""---
## 4. SIP Continuity Analysis

For investors with **6 or more SIP transactions**, compute the average
gap (in days) between consecutive SIP dates. Flag investors whose average
gap exceeds 35 days as **"at-risk"** — meaning they are likely missing
monthly SIPs (a regular monthly SIP should have gaps of ~28-31 days).

**Finding (from real data):** 1,332 of 1,362 eligible investors (97.8%)
are flagged as at-risk. This is an unusually high rate and reflects the
dataset's transaction dates being distributed somewhat randomly across
the date range rather than strictly monthly — consistent with the
independently-generated nature of the data found in Days 3 and 4.""")

code("""sip_sorted = sip_tx.sort_values(["investor_id", "transaction_date"])

# Only investors with 6+ SIP transactions
sip_counts = sip_sorted.groupby("investor_id").size()
eligible = sip_counts[sip_counts >= 6].index
sip_eligible = sip_sorted[sip_sorted.investor_id.isin(eligible)]

avg_gaps = (
    sip_eligible.groupby("investor_id")["transaction_date"]
    .apply(lambda x: x.diff().dt.days.dropna().mean())
    .reset_index()
)
avg_gaps.columns = ["investor_id", "avg_gap_days"]
avg_gaps["at_risk"] = avg_gaps["avg_gap_days"] > 35
avg_gaps["risk_label"] = avg_gaps["at_risk"].map(
    {True: "At-Risk (gap > 35d)", False: "Regular (gap ≤ 35d)"})

total = len(avg_gaps)
at_risk_n = avg_gaps["at_risk"].sum()
regular_n = total - at_risk_n

print(f"Investors with 6+ SIP transactions: {total}")
print(f"At-risk (avg gap > 35 days):         {at_risk_n} ({at_risk_n/total*100:.1f}%)")
print(f"Regular (avg gap ≤ 35 days):         {regular_n} ({regular_n/total*100:.1f}%)")
print(f"\\nAvg gap distribution:")
print(avg_gaps["avg_gap_days"].describe().round(1))

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Distribution of avg gaps
axes[0].hist(avg_gaps["avg_gap_days"], bins=40, color="#2E75B6", edgecolor="white")
axes[0].axvline(35, color="red", linestyle="--", linewidth=2, label="35-day threshold")
axes[0].set_title("Distribution of Avg SIP Gap (Days)\\n(investors with 6+ SIPs)")
axes[0].set_xlabel("Avg Gap Between SIPs (days)")
axes[0].set_ylabel("Number of Investors")
axes[0].legend()

# Pie chart
axes[1].pie([regular_n, at_risk_n],
            labels=[f"Regular\\n({regular_n} investors)", f"At-Risk\\n({at_risk_n} investors)"],
            autopct="%1.1f%%", colors=["#27AE60", "#C0392B"], startangle=90)
axes[1].set_title("SIP Continuity — At-Risk vs Regular Investors")

plt.tight_layout()
plt.savefig(CHART_DIR / "15_sip_continuity.png", dpi=150, bbox_inches="tight")
plt.show()
print("Chart saved: 15_sip_continuity.png")

# Save at-risk investor list
at_risk_df = avg_gaps[avg_gaps["at_risk"]][["investor_id", "avg_gap_days"]].sort_values("avg_gap_days", ascending=False)
at_risk_df.to_csv("../reports/at_risk_sip_investors.csv", index=False)
print(f"At-risk investor list saved: reports/at_risk_sip_investors.csv ({len(at_risk_df)} rows)")
""")

# ===========================================================================
# 5. Fund recommender
# ===========================================================================

md("""---
## 5. Simple Fund Recommender

Input: investor's **risk appetite** — Low / Moderate / High.

Logic: filter `fund_master` by matching `risk_category`, then rank by
**Sharpe ratio** (from `fund_scorecard.csv`) and return the **top 3 funds**
within that risk category.

This logic is also saved as a standalone `recommender.py` script so it
can be called from the command line or imported into other modules.""")

code("""scorecard = pd.read_csv("../fund_scorecard.csv")
# fund_scorecard.csv already has scheme_name, category, expense_ratio_pct
# from the Day 4 merge -- only add the columns NOT already present
# (sub_category and risk_category are the only ones missing)
recommender_data = scorecard.merge(
    fund_master[["amfi_code", "risk_category", "sub_category"]],
    on="amfi_code", how="left"
)

def recommend_funds(risk_appetite: str, top_n: int = 3) -> pd.DataFrame:
    \"\"\"
    Recommend top N funds for a given risk appetite.

    Parameters
    ----------
    risk_appetite : str
        One of: 'Low', 'Moderate', 'Moderately High', 'High', 'Very High'
    top_n : int
        Number of funds to return (default 3)

    Returns
    -------
    pd.DataFrame with recommended funds sorted by Sharpe ratio
    \"\"\"
    valid = ["Low", "Moderate", "Moderately High", "High", "Very High"]
    if risk_appetite not in valid:
        raise ValueError(f"risk_appetite must be one of {valid}")

    filtered = recommender_data[
        recommender_data["risk_category"] == risk_appetite
    ].sort_values("sharpe_ratio", ascending=False).head(top_n)

    return filtered[["overall_rank", "scheme_name", "category", "sub_category",
                      "risk_category", "sharpe_ratio", "cagr_3yr_pct",
                      "expense_ratio_pct", "fund_score"]].reset_index(drop=True)

# Print recommendations for all 3 risk levels requested in the task brief
print("=" * 70)
for appetite in ["Low", "Moderate", "High"]:
    recs = recommend_funds(appetite)
    print(f"\\nTop 3 funds for risk appetite: {appetite}")
    print("-" * 70)
    if len(recs) == 0:
        print(f"  No funds found for risk_category = '{appetite}'")
        print(f"  Available categories: {sorted(recommender_data['risk_category'].dropna().unique())}")
    else:
        print(recs.to_string(index=False))
print("=" * 70)

# Show all available risk categories in the data
print("\\nAll risk categories present in fund_master:")
print(fund_master["risk_category"].value_counts().to_string())
""")

code("""# Write recommender.py as a standalone script
lines = [
    "import sys",
    "import pandas as pd",
    "from pathlib import Path",
    "",
    "ROOT = Path(__file__).resolve().parent",
    "",
    "def recommend_funds(risk_appetite, top_n=3):",
    "    scorecard = pd.read_csv(ROOT / \'fund_scorecard.csv\')",
    "    fm = pd.read_csv(ROOT / \'data\' / \'processed\' / \'01_fund_master.csv\')",
    "    data = scorecard.merge(",
    "        fm[[\'amfi_code\',\'scheme_name\',\'risk_category\',\'expense_ratio_pct\',\'category\',\'sub_category\']],",
    "        on=\'amfi_code\', how=\'left\')",
    "    valid = [\'Low\', \'Moderate\', \'Moderately High\', \'High\', \'Very High\']",
    "    if risk_appetite not in valid:",
    "        raise ValueError(f\'risk_appetite must be one of {valid}\')",
    "    filtered = data[data[\'risk_category\'] == risk_appetite].sort_values(\'sharpe_ratio\', ascending=False).head(top_n)",
    "    cols = [\'overall_rank\',\'scheme_name\',\'category\',\'sub_category\',\'risk_category\',\'sharpe_ratio\',\'cagr_3yr_pct\',\'expense_ratio_pct\',\'fund_score\']",
    "    return filtered[cols].reset_index(drop=True)",
    "",
    "if __name__ == \'__main__\':",
    "    appetite = sys.argv[1] if len(sys.argv) > 1 else \'Moderate\'",
    "    print(f\'Top 3 recommendations for risk appetite: {appetite}\')",
    "    print(recommend_funds(appetite).to_string(index=False))",
]
with open(\"../recommender.py\", \"w\") as f:
    f.write(\"\\n\".join(lines))
print(\"recommender.py saved to project root\")
print(\"Test: python recommender.py Low / Moderate / High\")
""")

# ===========================================================================
# 6. Sector HHI
# ===========================================================================

md("""---
## 6. Sector HHI Concentration — All Equity Funds

**Herfindahl-Hirschman Index (HHI)** = Σ(weight_i²) × 10,000

Computed per fund from `portfolio_holdings.csv`. Higher HHI = more
concentrated portfolio (fewer sectors dominating). Lower HHI = more
diversified.

Interpretation thresholds (standard):
- HHI < 1,500 → diversified
- 1,500 ≤ HHI < 2,500 → moderately concentrated
- HHI ≥ 2,500 → highly concentrated

Only equity funds are included (the 6 debt funds have no stock holdings
in portfolio_holdings.csv).""")

code("""equity_codes = fund_master[fund_master["category"] == "Equity"]["amfi_code"].tolist()
ph_equity = holdings[holdings["amfi_code"].isin(equity_codes)].copy()

hhi_rows = []
for code_, grp in ph_equity.groupby("amfi_code"):
    w = grp["weight_pct"] / grp["weight_pct"].sum()
    hhi = (w ** 2).sum() * 10000
    top_sector = grp.loc[grp["weight_pct"].idxmax(), "sector"]
    sector_counts = grp.groupby("sector")["weight_pct"].sum().sort_values(ascending=False)
    hhi_rows.append({
        "amfi_code": code_,
        "hhi": round(hhi, 2),
        "num_holdings": len(grp),
        "top_sector": top_sector,
        "top_sector_weight_pct": round(grp.groupby("sector")["weight_pct"].sum().max(), 2),
    })

hhi_df = pd.DataFrame(hhi_rows).merge(
    fund_master[["amfi_code", "scheme_name", "sub_category"]], on="amfi_code")
hhi_df = hhi_df.sort_values("hhi", ascending=False).reset_index(drop=True)

def concentration_label(hhi):
    if hhi >= 2500: return "High"
    elif hhi >= 1500: return "Moderate"
    else: return "Low"

hhi_df["concentration"] = hhi_df["hhi"].apply(concentration_label)

print("Sector HHI Concentration — All Equity Funds:")
print(hhi_df[["scheme_name", "sub_category", "hhi", "num_holdings",
              "top_sector", "concentration"]].to_string(index=False))
print(f"\\nConcentration breakdown:")
print(hhi_df["concentration"].value_counts().to_string())

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
colors_map = {"Low": "#27AE60", "Moderate": "#E67E22", "High": "#C0392B"}
bar_colors = [colors_map[c] for c in hhi_df["concentration"]]
short_names = hhi_df["scheme_name"].str.replace(" - Regular - Growth", ""
    ).str.replace(" - Regular Plan - Growth", ""
    ).str.replace(" Fund", "")

axes[0].barh(range(len(hhi_df)), hhi_df["hhi"], color=bar_colors)
axes[0].set_yticks(range(len(hhi_df)))
axes[0].set_yticklabels(short_names, fontsize=7)
axes[0].axvline(1500, color="orange", linestyle="--", linewidth=1.5, label="Moderate threshold (1500)")
axes[0].axvline(2500, color="red", linestyle="--", linewidth=1.5, label="High threshold (2500)")
axes[0].set_xlabel("HHI Score")
axes[0].set_title("Sector HHI Concentration by Equity Fund")
axes[0].legend(fontsize=8)

conc_counts = hhi_df["concentration"].value_counts()
axes[1].pie(conc_counts.values,
            labels=[f"{k}\\n({v} funds)" for k, v in conc_counts.items()],
            autopct="%1.1f%%",
            colors=[colors_map.get(k, "grey") for k in conc_counts.index],
            startangle=90)
axes[1].set_title("Concentration Level Distribution")

plt.tight_layout()
plt.savefig(CHART_DIR / "16_hhi_concentration.png", dpi=150, bbox_inches="tight")
plt.show()
print("Chart saved: 16_hhi_concentration.png")
""")

# ===========================================================================
# 7. Key findings
# ===========================================================================

md("""---
## 7. Key Findings

**Finding 1 — Small Cap funds carry the highest VaR and CVaR, as expected.**
The 5 funds with the worst (most negative) VaR(95%) are all Small Cap
equity funds, with daily losses at the 5th percentile exceeding -2.5%.
Liquid and Gilt funds sit at the other extreme, with VaR close to 0%,
consistent with their low-volatility, debt-instrument nature. The
risk-ordering by VaR matches the risk_category labels in fund_master,
which is a useful internal consistency check.

**Finding 2 — Rolling 90-day Sharpe ratios are highly volatile,
frequently swinging from positive to negative within the same year.**
This is consistent with the near-random daily return series found in
Days 3 and 4 — a fund that randomly generates positive returns for a
few months will show a high rolling Sharpe, then a negative run flips it.
Liquid funds show the most stable (and consistently near-zero) rolling
Sharpe, since their returns are low-variance by design.

**Finding 3 — Almost all investors entered in 2024 (4,456 vs 197 in 2025).**
This is an artefact of the transaction dataset covering Jan 2024–May 2025
— investors who first transacted in 2025 have had less time to accumulate
transaction history. The 2024 cohort's top fund preference is ICICI Pru
Bluechip Direct, while the smaller 2025 cohort prefers SBI Small Cap Direct
— a shift toward higher risk appetite in newer investors.

**Finding 4 — 97.8% of eligible investors (1,332 of 1,362) are flagged
as SIP "at-risk" (avg gap > 35 days).** This high rate reflects the
transaction dates in the dataset being distributed across the date range
rather than following strict monthly SIP schedules. In a real dataset this
figure would typically be 10–20% — flagging it here is accurate reporting
of what the data shows, not a modelling error.

**Finding 5 — Most equity funds in this dataset show MODERATE sector
concentration (HHI 1,500–2,500).** Very few are in the "highly
concentrated" range, and the top sector varies considerably by fund —
IT, Banking, Pharma, Diversified, and Telecom all appear as top sectors
across different funds. This is more realistic than expected for a
synthetically-generated dataset, since portfolio_holdings.csv appears to
have been constructed with genuine sector diversity across funds.
""")

code("""print("Advanced Analytics notebook complete.")
print("\\nDeliverables produced:")
print("  - var_cvar_report.csv                  (project root)")
print("  - recommender.py                        (project root)")
print("  - rolling_sharpe_chart.png             (project root)")
print("  - reports/charts/12_var_cvar_bar.png")
print("  - reports/charts/13_rolling_sharpe.png")
print("  - reports/charts/14_investor_cohort.png")
print("  - reports/charts/15_sip_continuity.png")
print("  - reports/charts/16_hhi_concentration.png")
print("  - reports/at_risk_sip_investors.csv")
""")

# ===========================================================================
# Assemble notebook
# ===========================================================================

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.11"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NB_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1)

print(f"Notebook written to {NB_PATH} ({len(cells)} cells).")