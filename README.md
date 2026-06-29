# Capstone Project (Vatsal)

**Day 1 — Project Setup + Data Ingestion (ETL)**

## 0. What's in this folder

```
Capstone Project (Vatsal)/
├── data/
│   ├── raw/            <- put your 10 provided CSVs here
│   └── processed/       <- cleaned/processed data goes here later
├── notebooks/           <- Jupyter notebooks
├── sql/                 <- SQL scripts
├── dashboard/           <- dashboard app files (later days)
├── reports/             <- generated reports (data quality summary lands here)
├── data_ingestion.py    <- loads + profiles all 10 CSVs, validates AMFI codes
├── live_nav_fetch.py    <- pulls live NAV data from mfapi.in
├── requirements.txt
├── .gitignore
└── README.md            <- this file
```

## 1. Open this in VS Code

1. Download/copy this whole folder onto your machine (e.g. `Desktop/Capstone Project (Vatsal)`).
2. In VS Code: **File → Open Folder...** → select `Capstone Project (Vatsal)`.
3. Open a terminal in VS Code: **Terminal → New Terminal**.

## 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Add your 10 datasets

Copy all 10 CSV files from your Drive folder into:

```
data/raw/
```

> The `data_ingestion.py` script tries to auto-detect which file is your
> "fund master" file and which is your "nav history" file by filename
> (it looks for names containing `fund_master`/`master` and `nav_history`/`nav`).
> If your filenames are different, either rename them or edit the
> `FUND_MASTER_HINTS` / `NAV_HISTORY_HINTS` lists near the top of the script.

## 5. Initialise Git and push to GitHub

```bash
git init
git add .
git commit -m "Day 1: Project setup"
```

Create an empty repo on GitHub (no README/license, so there's no conflict), then:

```bash
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git branch -M main
git push -u origin main
```

## 6. Run the ingestion script

```bash
python data_ingestion.py
```

This will:
- Load every CSV in `data/raw/`.
- Print `.shape`, `.dtypes`, `.head()` and an anomaly check (nulls, duplicates,
  empty columns) for each file.
- Print unique fund houses, categories, sub-categories, and risk grades from
  the fund master file.
- Cross-check that every AMFI/scheme code in fund_master exists in nav_history
  (and vice versa), printing any mismatches.
- Write a full summary to `reports/day1_data_quality_summary.md`.

**If a column isn't auto-detected:** the script will print a warning telling
you exactly which logical column (e.g. `risk_grade`) it couldn't find in
which file. Open that CSV, check the real column name, and add it to the
matching list inside `COLUMN_ALIASES` near the top of `data_ingestion.py`.

## 7. Run the live NAV fetch script

```bash
python live_nav_fetch.py
```

This will:
- Call `https://api.mfapi.in/mf/{scheme_code}` for the HDFC Top 100 code
  given in the task brief (125497) and the 5 key schemes (SBI Bluechip,
  ICICI Bluechip, Nippon Large Cap, Axis Bluechip, Kotak Bluechip).
- Save each scheme's full NAV history as its own raw CSV in `data/raw/`
  (e.g. `nav_125497.csv`).
- Save a combined file `data/raw/live_nav_combined.csv`.
- Save a fetch summary `data/raw/live_nav_fetch_summary.csv`.

> **Heads up:** when I tested this live, scheme code `125497` actually
> returned **"SBI Small Cap Fund"**, not "HDFC Top 100" as labeled in the
> task brief. The script prints the real `scheme_name` from the API and
> flags the mismatch — worth a line in your data quality summary as a
> real-world example of why you validate source data instead of trusting
> labels blindly.

## 8. Commit your Day 1 work

```bash
git add .
git commit -m "Day 1: Data ingestion complete"
git push
```

## Deliverables checklist (per the task brief)

- [x] `data_ingestion.py`
- [x] `live_nav_fetch.py`
- [x] `requirements.txt`
- [ ] GitHub repo with Day 1 commit (do steps 5 and 8 above)
