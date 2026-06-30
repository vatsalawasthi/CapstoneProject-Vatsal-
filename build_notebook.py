"""
build_notebook.py
-------------------
Generates notebooks/EDA_Analysis.ipynb for Day 3 (Exploratory Data Analysis).

This script builds the notebook's JSON structure directly (an .ipynb file is
just JSON conforming to the Jupyter notebook schema) rather than requiring
the `nbformat` package, so it has no extra dependencies beyond what's
already in requirements.txt.

Every chart and number in this notebook is computed from your real cleaned
CSVs in data/processed/ -- nothing here is sample/demo data. A few of the
task brief's framing claims (e.g. "2023 bull run / 2024 corrections") don't
actually hold in this dataset (see the markdown insight cells), so the
notebook reports what the data actually shows rather than forcing a
narrative that isn't there.

Run:
    python build_notebook.py
"""

import json
from pathlib import Path

NB_PATH = Path(__file__).resolve().parent / "notebooks" / "EDA_Analysis.ipynb"

cells = []


def md(text: str):
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": text.splitlines(keepends=True),
    })


def code(text: str):
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.splitlines(keepends=True),
    })


# ===========================================================================
# Title + setup
# ===========================================================================

md("""# Day 3 — Exploratory Data Analysis (EDA)
## Bluestock Mutual Fund Capstone

This notebook explores the cleaned datasets produced in Day 2
(`data/processed/`) and the SQLite star schema in `bluestock_mf.db`.

All charts below are built directly from the real cleaned CSVs delivered
in this project — nothing here is sample or placeholder data.

**Sections:**
1. NAV trend analysis (all 40 schemes, 2022–2026)
2. AUM growth by fund house (2022–2025)
3. SIP inflow time-series (Jan 2022 – Dec 2025)
4. Category inflow heatmap
5. Investor demographics
6. Geographic distribution
7. Folio count growth
8. NAV return correlation matrix (10 selected funds)
9. Sector allocation donut
10. Key findings summary
""")

code("""# Setup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)

DATA_DIR = Path("..") / "data" / "processed"
CHART_DIR = Path("..") / "reports" / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

print("Loading cleaned datasets from data/processed/ ...")
fund_master   = pd.read_csv(DATA_DIR / "01_fund_master.csv")
nav_history   = pd.read_csv(DATA_DIR / "02_nav_history.csv", parse_dates=["date"])
aum_by_house  = pd.read_csv(DATA_DIR / "03_aum_by_fund_house.csv", parse_dates=["date"])
sip_inflows   = pd.read_csv(DATA_DIR / "04_monthly_sip_inflows.csv")
cat_inflows   = pd.read_csv(DATA_DIR / "05_category_inflows.csv")
folio_count   = pd.read_csv(DATA_DIR / "06_industry_folio_count.csv")
scheme_perf   = pd.read_csv(DATA_DIR / "07_scheme_performance.csv")
transactions  = pd.read_csv(DATA_DIR / "08_investor_transactions.csv", parse_dates=["transaction_date"])
holdings      = pd.read_csv(DATA_DIR / "09_portfolio_holdings.csv")
benchmarks    = pd.read_csv(DATA_DIR / "10_benchmark_indices.csv", parse_dates=["date"])

print(f"fund_master:   {fund_master.shape}")
print(f"nav_history:   {nav_history.shape}")
print(f"aum_by_house:  {aum_by_house.shape}")
print(f"sip_inflows:   {sip_inflows.shape}")
print(f"cat_inflows:   {cat_inflows.shape}")
print(f"folio_count:   {folio_count.shape}")
print(f"scheme_perf:   {scheme_perf.shape}")
print(f"transactions:  {transactions.shape}")
print(f"holdings:      {holdings.shape}")
print(f"benchmarks:    {benchmarks.shape}")
""")

# ===========================================================================
# 1. NAV trend analysis
# ===========================================================================

md("""---
## 1. NAV Trend Analysis — All 40 Schemes (2022–2026)

Plotting daily NAV for every scheme. The task brief asks us to highlight a
"2023 bull run" and "2024 market corrections" — but as the chart and the
year-over-year growth table below show, **this dataset does not actually
contain a bull run or a correction**: average NAV grows smoothly at
roughly 12–14% every single year with no drawdown. We annotate the real
year-over-year growth rates instead of inventing events that aren't in
the data (see Finding #1 in the summary).""")

code("""# Year-over-year average NAV growth (across all 40 funds) -- check whether
# a "2023 bull run" / "2024 correction" narrative actually holds in this data
nav_history["year"] = nav_history["date"].dt.year
yearly_avg_nav = nav_history.groupby("year")["nav"].mean()
yearly_growth_pct = yearly_avg_nav.pct_change() * 100

print("Average NAV by year (all 40 funds):")
print(yearly_avg_nav.round(2))
print("\\nYoY growth %:")
print(yearly_growth_pct.round(2))
""")

code("""# Interactive Plotly chart: daily NAV for all 40 schemes
fig = px.line(
    nav_history,
    x="date", y="nav", color="amfi_code",
    title="Daily NAV — All 40 Schemes (2022–2026)",
    labels={"nav": "NAV (INR)", "date": "Date", "amfi_code": "AMFI Code"},
)

# Annotate each year's actual YoY growth rate (real numbers, not invented events)
for yr, growth in yearly_growth_pct.dropna().items():
    fig.add_annotation(
        x=f"{yr}-07-01", y=nav_history["nav"].max() * 0.95,
        text=f"{yr}: {growth:+.1f}% YoY",
        showarrow=False, font=dict(size=10, color="black"),
    )

fig.update_layout(showlegend=False, height=600)
fig.write_image(str(CHART_DIR / "01_nav_trend_all_schemes.png"), scale=2)
fig.show()
""")

# ===========================================================================
# 2. AUM growth bar chart
# ===========================================================================

md("""---
## 2. AUM Growth by Fund House (2022–2025)

Grouped bar chart of year-end AUM per fund house. **SBI Mutual Fund is
confirmed as the dominant fund house, reaching ₹12.5 lakh crore by 2025**
— exactly matching the figure called out in the task brief.""")

code("""# Year-end AUM snapshot per fund house, per year
aum_by_house["year"] = aum_by_house["date"].dt.year
yearly_aum = (
    aum_by_house.sort_values("date")
    .groupby(["fund_house", "year"])["aum_crore"].last()
    .reset_index()
)
yearly_aum["aum_lakh_cr"] = yearly_aum["aum_crore"] / 100000

print("SBI 2025 AUM:", yearly_aum.query("fund_house == 'SBI Mutual Fund' and year == 2025")["aum_lakh_cr"].values[0], "lakh crore")

plt.figure(figsize=(14, 7))
ax = sns.barplot(
    data=yearly_aum, x="fund_house", y="aum_lakh_cr", hue="year",
    palette="viridis",
)
ax.set_title("AUM by Fund House, Year-End Snapshot (2022–2025)", fontsize=14)
ax.set_xlabel("Fund House")
ax.set_ylabel("AUM (₹ Lakh Crore)")
plt.xticks(rotation=30, ha="right")

# Highlight SBI's 2025 dominance -- find SBI's x-position on the categorical
# axis dynamically (don't hardcode index 0, since bar order follows groupby)
fund_house_order = [t.get_text() for t in ax.get_xticklabels()]
sbi_x = fund_house_order.index("SBI Mutual Fund")
sbi_2025 = yearly_aum.query("fund_house == 'SBI Mutual Fund' and year == 2025")["aum_lakh_cr"].values[0]
ax.annotate(
    f"SBI 2025: ₹{sbi_2025:.2f}L Cr\\n(industry leader)",
    xy=(sbi_x, sbi_2025), xytext=(sbi_x - 2.3, sbi_2025 + 2),
    arrowprops=dict(arrowstyle="->", color="darkred"),
    fontsize=10, color="darkred", fontweight="bold",
)
plt.legend(title="Year", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.savefig(CHART_DIR / "02_aum_growth_by_fund_house.png", dpi=150, bbox_inches="tight")
plt.show()
""")

# ===========================================================================
# 3. SIP inflow time-series
# ===========================================================================

md("""---
## 3. SIP Inflow Time-Series (Jan 2022 – Dec 2025)

Monthly SIP inflow trend with the all-time high annotated. **₹31,002 crore
in December 2025 is confirmed as the all-time high** in this dataset,
exactly matching the task brief.""")

code("""# Confirm the all-time high
max_row = sip_inflows.loc[sip_inflows["sip_inflow_crore"].idxmax()]
print(f"All-time high SIP inflow: ₹{max_row['sip_inflow_crore']:,.0f} crore in {max_row['month']}")

fig = px.line(
    sip_inflows, x="month", y="sip_inflow_crore",
    title="Monthly SIP Inflow (Jan 2022 – Dec 2025)",
    labels={"sip_inflow_crore": "SIP Inflow (₹ Crore)", "month": "Month"},
    markers=True,
)
fig.add_annotation(
    x=max_row["month"], y=max_row["sip_inflow_crore"],
    text=f"All-time high: ₹{max_row['sip_inflow_crore']:,.0f} Cr (Dec 2025)",
    showarrow=True, arrowhead=2, ax=-60, ay=-50,
    font=dict(size=11, color="darkgreen"),
)
fig.update_xaxes(tickangle=45, nticks=24)
fig.update_layout(height=550)
fig.write_image(str(CHART_DIR / "03_sip_inflow_timeseries.png"), scale=2)
fig.show()
""")

# ===========================================================================
# 4. Category inflow heatmap
# ===========================================================================

md("""---
## 4. Category Inflow Heatmap

**Data coverage note:** `category_inflows.csv` only covers 12 months
(April 2024 – March 2025), not the full 2022–2026 range available in the
other datasets. The heatmap below reflects that actual coverage rather
than implying a longer history that isn't in the source file.""")

code("""cat_pivot = cat_inflows.pivot(index="category", columns="month", values="net_inflow_crore")
# order columns chronologically
cat_pivot = cat_pivot[sorted(cat_pivot.columns)]

plt.figure(figsize=(14, 7))
ax = sns.heatmap(
    cat_pivot, cmap="RdYlGn", center=0, annot=True, fmt=".0f",
    linewidths=0.5, cbar_kws={"label": "Net Inflow (₹ Crore)"},
)
ax.set_title("Net Category Inflows by Month (Apr 2024 – Mar 2025)", fontsize=14)
ax.set_xlabel("Month")
ax.set_ylabel("Fund Category")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(CHART_DIR / "04_category_inflow_heatmap.png", dpi=150, bbox_inches="tight")
plt.show()
""")

# ===========================================================================
# 5. Investor demographics
# ===========================================================================

md("""---
## 5. Investor Demographics

Age group distribution, SIP amount by age group, and gender split — based
on the 5,000 unique investors in `investor_transactions.csv`.""")

code("""investors = transactions.drop_duplicates("investor_id")
sip_tx = transactions[transactions["transaction_type"] == "SIP"]

fig, axes = plt.subplots(1, 3, figsize=(20, 6))

# 5a. Age group pie chart
age_counts = investors["age_group"].value_counts().sort_index()
axes[0].pie(
    age_counts.values, labels=age_counts.index, autopct="%1.1f%%",
    colors=sns.color_palette("pastel"), startangle=90,
)
axes[0].set_title("Investor Age Group Distribution")

# 5b. SIP amount box plot by age group
order = ["18-25", "26-35", "36-45", "46-55", "56+"]
sns.boxplot(data=sip_tx, x="age_group", y="amount_inr", order=order, hue="age_group",
            hue_order=order, legend=False, ax=axes[1], palette="Set2")
axes[1].set_title("SIP Amount Distribution by Age Group")
axes[1].set_xlabel("Age Group")
axes[1].set_ylabel("SIP Amount (₹)")

# 5c. Gender split
gender_counts = investors["gender"].value_counts()
axes[2].pie(
    gender_counts.values, labels=gender_counts.index, autopct="%1.1f%%",
    colors=["#6699CC", "#FF99CC"], startangle=90,
)
axes[2].set_title("Investor Gender Split")

plt.tight_layout()
plt.savefig(CHART_DIR / "05_investor_demographics.png", dpi=150, bbox_inches="tight")
plt.show()

print("Age group breakdown:")
print((age_counts / age_counts.sum() * 100).round(1))
print("\\nGender breakdown:")
print((gender_counts / gender_counts.sum() * 100).round(1))
""")

# ===========================================================================
# 6. Geographic distribution
# ===========================================================================

md("""---
## 6. Geographic Distribution

SIP amount by state, and the T30 (top 30 cities) vs B30 (beyond top 30)
city-tier split.""")

code("""fig, axes = plt.subplots(1, 2, figsize=(18, 7))

# 6a. Horizontal bar: SIP amount by state
state_sip = sip_tx.groupby("state")["amount_inr"].sum().sort_values()
axes[0].barh(state_sip.index, state_sip.values / 1e7, color=sns.color_palette("crest", len(state_sip)))
axes[0].set_title("Total SIP Amount by State")
axes[0].set_xlabel("SIP Amount (₹ Crore)")

# 6b. T30 vs B30 pie chart
tier_counts = investors["city_tier"].value_counts()
axes[1].pie(
    tier_counts.values, labels=tier_counts.index, autopct="%1.1f%%",
    colors=["#FFA07A", "#87CEEB"], startangle=90, explode=(0.03, 0.03),
)
axes[1].set_title("T30 vs B30 City Tier Split (Investors)")

plt.tight_layout()
plt.savefig(CHART_DIR / "06_geographic_distribution.png", dpi=150, bbox_inches="tight")
plt.show()

print("Top 5 states by SIP amount:")
print((state_sip / 1e7).round(2).sort_values(ascending=False).head())
print("\\nCity tier split:", dict((tier_counts / tier_counts.sum() * 100).round(1)))
""")

# ===========================================================================
# 7. Folio count growth
# ===========================================================================

md("""---
## 7. Folio Count Growth

Total industry folio count, confirmed growing **from 13.26 crore (Jan 2022)
to 26.12 crore (Dec 2025)** — almost exactly doubling, matching the task
brief's figures.""")

code("""folio_sorted = folio_count.sort_values("month")
start_val = folio_sorted.iloc[0]
end_val = folio_sorted.iloc[-1]
print(f"Folio count: {start_val['total_folios_crore']} Cr ({start_val['month']}) -> "
      f"{end_val['total_folios_crore']} Cr ({end_val['month']})")
print(f"Growth: {(end_val['total_folios_crore']/start_val['total_folios_crore'] - 1)*100:.1f}%")

fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(folio_sorted["month"], folio_sorted["total_folios_crore"], marker="o", linewidth=2, color="#2E86AB")
ax.set_title("Total Investor Folio Count Growth (Jan 2022 – Dec 2025)", fontsize=14)
ax.set_xlabel("Month")
ax.set_ylabel("Total Folios (₹ Crore)")
plt.xticks(rotation=45, ha="right")

# Mark key milestones: start, crossing 20 Cr, and end
ax.annotate(f"Start: {start_val['total_folios_crore']} Cr",
            xy=(start_val["month"], start_val["total_folios_crore"]),
            xytext=(0, 15), textcoords="offset points", ha="center", fontsize=9, color="darkblue")
crossing_20 = folio_sorted[folio_sorted["total_folios_crore"] >= 20].iloc[0]
ax.annotate(f"Crossed 20 Cr: {crossing_20['month']}",
            xy=(crossing_20["month"], crossing_20["total_folios_crore"]),
            xytext=(0, 15), textcoords="offset points", ha="center", fontsize=9, color="darkorange")
ax.annotate(f"End: {end_val['total_folios_crore']} Cr",
            xy=(end_val["month"], end_val["total_folios_crore"]),
            xytext=(0, -20), textcoords="offset points", ha="center", fontsize=9, color="darkgreen")

plt.tight_layout()
plt.savefig(CHART_DIR / "07_folio_count_growth.png", dpi=150, bbox_inches="tight")
plt.show()
""")

# ===========================================================================
# 8. NAV return correlation matrix
# ===========================================================================

md("""---
## 8. NAV Return Correlation Matrix (10 Selected Funds)

Pairwise correlation of **daily returns** (not raw NAV levels) for 10
funds spanning large cap, mid cap, small cap, flexicap, index, gilt, and
liquid categories across 6 fund houses.

**Important finding:** the correlations below are close to zero across
the board — including between the Regular and Direct plans of the *same*
underlying fund, which in real markets are virtually identical (they hold
the same portfolio, differing only in expense ratio) and should show
correlation near +1.0. This is strong evidence that each fund's NAV
series in this dataset was generated independently rather than driven by
a shared underlying market. See Finding #8 in the summary for the full
discussion — this is reported honestly rather than papered over.""")

code("""selected_codes = [119551, 119598, 119120, 100016, 100033, 120503, 120507, 118634, 120843, 102885]
name_map = fund_master.set_index("amfi_code")["scheme_name"].to_dict()

# Sanity check: Regular vs Direct plan of the SAME fund (SBI Bluechip) --
# these should be ~+1.0 correlated in real markets since they hold identical
# portfolios. We check this explicitly to validate the finding above.
nav_orig = nav_history[nav_history["is_filled"] == False].copy()
pivot_check = nav_orig[nav_orig.amfi_code.isin([119551, 119552])].pivot(index="date", columns="amfi_code", values="nav")
returns_check = pivot_check.pct_change().dropna()
same_fund_corr = returns_check[119551].corr(returns_check[119552])
print(f"Sanity check -- SBI Bluechip Regular vs Direct (same fund, different plan) "
      f"return correlation: {same_fund_corr:.4f}")
print("(In a real market this should be close to +1.0 since both plans hold an "
      "identical portfolio -- a near-zero result confirms the NAV series are "
      "generated independently per fund, not from a shared market.)")

# Build the 10-fund correlation matrix
nav_sel = nav_orig[nav_orig.amfi_code.isin(selected_codes)]
pivot = nav_sel.pivot(index="date", columns="amfi_code", values="nav")
returns = pivot.pct_change().dropna()
corr = returns.corr().rename(index=name_map, columns=name_map)

# shorten labels for readability
short_names = {c: c.replace(" Fund", "").replace(" - Regular Plan - Growth", "")
                    .replace(" - Regular - Growth", "") for c in corr.columns}
corr_short = corr.rename(index=short_names, columns=short_names)

plt.figure(figsize=(11, 9))
sns.heatmap(corr_short, annot=True, fmt=".2f", cmap="coolwarm", center=0,
            square=True, linewidths=0.5, cbar_kws={"label": "Correlation"})
plt.title("Daily Return Correlation — 10 Selected Funds", fontsize=14)
plt.xticks(rotation=45, ha="right")
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(CHART_DIR / "08_nav_return_correlation_matrix.png", dpi=150, bbox_inches="tight")
plt.show()
""")

# ===========================================================================
# 9. Sector allocation donut
# ===========================================================================

md("""---
## 9. Sector Allocation Donut Chart

Aggregate sector weights from `portfolio_holdings.csv`, summed by market
value across all 34 equity funds in the dataset (the 6 debt funds have no
stock holdings, so they're correctly excluded).""")

code("""sector_totals = holdings.groupby("sector")["market_value_cr"].sum().sort_values(ascending=False)
print("Sector exposure (₹ Crore):")
print(sector_totals)
print(f"\\nTotal across all equity holdings: ₹{sector_totals.sum():,.0f} Cr")
print(f"Top sector ({sector_totals.index[0]}) share: {sector_totals.iloc[0]/sector_totals.sum()*100:.1f}%")

fig = go.Figure(data=[go.Pie(
    labels=sector_totals.index, values=sector_totals.values,
    hole=0.45, textinfo="label+percent",
    marker=dict(colors=px.colors.qualitative.Set3),
)])
fig.update_layout(
    title="Sector Allocation Across All Equity Fund Holdings",
    height=600, showlegend=True,
)
fig.write_image(str(CHART_DIR / "09_sector_allocation_donut.png"), scale=2)
fig.show()
""")

# ===========================================================================
# 10. Key findings summary
# ===========================================================================

md("""---
## 10. Key EDA Findings

**Finding 1 — NAV growth is smooth and steady, not a "bull run + correction" pattern.**
Average NAV across all 40 funds grew at a remarkably consistent ~12–14% per
year from 2022 through 2026, with no visible drawdown in 2024. The task
brief's framing of a "2023 bull run" and "2024 market correction" doesn't
match what's actually in this dataset — there's no year where average NAV
fell. *(Chart 1: NAV Trend Analysis)*

**Finding 2 — SBI Mutual Fund is the clear AUM leader, exactly as expected.**
SBI's AUM grew from ₹6.05L Cr (2022) to ₹12.5L Cr (2025) — nearly double —
and it has held the #1 spot among all 10 fund houses in every year of the
dataset. ICICI Prudential MF is a distant second at ₹10.74L Cr by 2025.
*(Chart 2: AUM Growth by Fund House)*

**Finding 3 — SIP inflows have grown almost 3x, peaking at an all-time high
in the final month of data.** Monthly SIP inflow rose from ₹11,517 Cr
(Jan 2022) to an all-time high of ₹31,002 Cr (Dec 2025) — confirming
sustained, accelerating retail participation in systematic investing.
*(Chart 3: SIP Inflow Time-Series)*

**Finding 4 — Category-level inflow data only covers a 12-month window.**
Unlike the other time series (which span 2022–2026), `category_inflows.csv`
only has data for April 2024 – March 2025. Within that window, Small Cap
funds consistently attracted larger net inflows than Large Cap funds most
months — a sign of strong retail risk appetite during this period.
*(Chart 4: Category Inflow Heatmap)*

**Finding 5 — Investors are predominantly young and male.** 40.7% of
investors are aged 26–35 (the single largest bracket), and just 7.8% are
56+. The investor base is 66.7% male vs 33.3% female — a 2:1 skew worth
noting for any future product or marketing strategy. SIP ticket sizes are
fairly similar across age groups (median ≈ ₹5,000–5,400), so the age skew
is about *participation*, not *amount invested per SIP*.
*(Chart 5: Investor Demographics)*

**Finding 6 — T30 cities dominate investor count and SIP value 2:1 over B30.**
66.7% of investors are from T30 (top-30) cities, and T30 SIP value
(₹14.49 Cr×10) is almost exactly double B30's (₹7.23 Cr×10) — mutual fund
penetration in India is still heavily concentrated in major cities, despite
years of "Mutual Funds Sahi Hai"-style campaigns targeting smaller towns.
Punjab, Madhya Pradesh, and Tamil Nadu are the top 3 states by SIP value.
*(Chart 6: Geographic Distribution)*

**Finding 7 — Investor folio count has almost exactly doubled.** Total
industry folios grew from 13.26 Cr (Jan 2022) to 26.12 Cr (Dec 2025) — a
97% increase — crossing the 20 Cr milestone around October 2024. This
tracks closely with the SIP inflow growth in Finding 3, consistent with
more retail investors entering via systematic plans.
*(Chart 7: Folio Count Growth)*

**Finding 8 — NAV return correlations are unexpectedly close to zero across
all 10 funds, including between two plans of the *same* fund.** SBI
Bluechip's Regular and Direct plans — which hold an identical underlying
portfolio and in any real market would be correlated above +0.95 — show a
return correlation of essentially 0 in this dataset. This indicates the
NAV time series were generated independently per fund rather than driven
by shared market movements. **This is a data-generation characteristic to
be aware of, not a market insight** — any "diversification benefit"
conclusions drawn from this correlation matrix would not reflect real-world
fund behavior.
*(Chart 8: NAV Return Correlation Matrix)*

**Finding 9 — Banking is the single largest sector exposure across equity
funds, at ₹62,840 Cr (≈20% of all tracked equity holdings' market value).**
IT (₹38,477 Cr) and Pharma (₹34,606 Cr) round out the top 3. This is
consistent with Banking & Financials typically carrying the heaviest
weight in Indian large-cap and flexicap portfolios.
*(Chart 9: Sector Allocation Donut)*

**Finding 10 — Lumpsum transactions carry far higher average ticket size
than SIP, as expected, but SIP dominates by transaction count.** SIP
accounts for 60% of all transactions (19,716 of 32,778) but only ~7% of
total transaction value, with a median ticket size around ₹5,000–11,000.
Lumpsum transactions average ₹2.54L per transaction — over 20x the typical
SIP amount — confirming SIP's role as a high-frequency, small-ticket
investing behavior versus lumpsum's occasional, large-value pattern.
*(Cross-reference: Day 2 queries.sql, Query 7)*
""")

code("""print("EDA notebook complete.")
print(f"Charts saved to: {CHART_DIR.resolve()}")
import os
for f in sorted(os.listdir(CHART_DIR)):
    print(" -", f)
""")


# ===========================================================================
# Assemble notebook JSON
# ===========================================================================

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.11",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NB_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1)

print(f"Notebook written to {NB_PATH} ({len(cells)} cells).")