"""
live_nav_fetch.py
-----------------
Day 1 Task: Fetch live NAV data from mfapi.in (https://www.mfapi.in/)

What this script does:
1. Hits GET https://api.mfapi.in/mf/{scheme_code} for:
      - 125497  -> labeled in the task brief as "HDFC Top 100 Direct"
      - 119551  -> SBI Bluechip
      - 120503  -> ICICI Bluechip
      - 118632  -> Nippon Large Cap
      - 119092  -> Axis Bluechip
      - 120841  -> Kotak Bluechip
2. Parses the JSON response (meta + historical NAV data).
3. Saves each scheme's full NAV history as a raw CSV in data/raw/.
4. Saves a combined CSV of all schemes (with scheme_code + scheme_name columns)
   for convenience in later analysis.
5. Flags any mismatch between the scheme name given in the task brief and the
   scheme name actually returned by the API (data-quality check).

Run:
    python live_nav_fetch.py
"""

import json
import time
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = "https://api.mfapi.in/mf/{code}"

# scheme_code -> name as given in the Day 1 task brief
SCHEMES = {
    125497: "HDFC Top 100 Direct (as labeled in task brief)",
    119551: "SBI Bluechip",
    120503: "ICICI Bluechip",
    118632: "Nippon Large Cap",
    119092: "Axis Bluechip",
    120841: "Kotak Bluechip",
}

OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REQUEST_TIMEOUT = 15  # seconds
RETRY_COUNT = 3
RETRY_DELAY = 2  # seconds between retries


def fetch_scheme(scheme_code: int):
    """Fetch NAV JSON for a single scheme code, with simple retry logic."""
    url = BASE_URL.format(code=scheme_code)
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, json.JSONDecodeError) as exc:
            print(f"  [attempt {attempt}/{RETRY_COUNT}] failed for {scheme_code}: {exc}")
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY)
    print(f"  ERROR: could not fetch scheme {scheme_code} after {RETRY_COUNT} attempts.")
    return None


def main():
    combined_frames = []
    summary_rows = []

    for code, label in SCHEMES.items():
        print(f"Fetching scheme {code} ({label}) ...")
        payload = fetch_scheme(code)

        if payload is None or payload.get("status") != "SUCCESS":
            summary_rows.append(
                {"scheme_code": code, "task_label": label, "api_scheme_name": None,
                 "rows_fetched": 0, "status": "FAILED"}
            )
            continue

        meta = payload.get("meta", {})
        data = payload.get("data", [])
        api_name = meta.get("scheme_name", "UNKNOWN")

        # Flag mismatches between task brief label and the actual API result
        if label.split(" (")[0].lower().split()[0] not in api_name.lower():
            print(f"  NOTE: task brief calls this '{label}', "
                  f"but the API returns scheme_name = '{api_name}'. "
                  f"Recording actual API name in the data and in the summary.")

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
        df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
        df["scheme_code"] = code
        df["scheme_name"] = api_name
        df["fund_house"] = meta.get("fund_house")
        df["scheme_category"] = meta.get("scheme_category")

        # Save individual raw CSV
        out_path = OUTPUT_DIR / f"nav_{code}.csv"
        df.to_csv(out_path, index=False)
        print(f"  Saved {len(df)} rows -> {out_path}")

        combined_frames.append(df)
        summary_rows.append(
            {"scheme_code": code, "task_label": label, "api_scheme_name": api_name,
             "rows_fetched": len(df), "status": "OK"}
        )

    # Combined file across all fetched schemes
    if combined_frames:
        combined = pd.concat(combined_frames, ignore_index=True)
        combined_path = OUTPUT_DIR / "live_nav_combined.csv"
        combined.to_csv(combined_path, index=False)
        print(f"\nSaved combined NAV file -> {combined_path} ({len(combined)} rows total)")

    # Fetch summary (useful input to the Day 1 data-quality summary)
    summary_df = pd.DataFrame(summary_rows)
    summary_path = OUTPUT_DIR / "live_nav_fetch_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"Saved fetch summary -> {summary_path}")
    print("\n", summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
