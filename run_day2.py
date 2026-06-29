"""
run_day2.py
------------
Convenience script: runs every Day 2 step in the correct order.

    1. clean_nav.py            -> data/processed/02_nav_history.csv
    2. clean_transactions.py   -> data/processed/08_investor_transactions.csv
    3. clean_performance.py    -> data/processed/07_scheme_performance.csv
    4. clean_others.py         -> the other 7 cleaned CSVs
    5. load_to_sqlite.py       -> bluestock_mf.db (schema + all data loaded)
    6. run_queries.py          -> prints all 10 analytical queries' results

Run:
    python run_day2.py
"""

import subprocess
import sys

STEPS = [
    "clean_nav.py",
    "clean_transactions.py",
    "clean_performance.py",
    "clean_others.py",
    "load_to_sqlite.py",
    "run_queries.py",
]


def main():
    for step in STEPS:
        print(f"\n{'#' * 70}\n# Running {step}\n{'#' * 70}")
        result = subprocess.run([sys.executable, step])
        if result.returncode != 0:
            print(f"\nSTOPPED: {step} exited with an error (code {result.returncode}). "
                  f"Fix the issue above before continuing.")
            sys.exit(result.returncode)

    print(f"\n{'#' * 70}\n# Day 2 pipeline complete.\n"
          f"# Deliverables: data/processed/*.csv, bluestock_mf.db, "
          f"sql/schema.sql, sql/queries.sql, data_dictionary.md\n{'#' * 70}")


if __name__ == "__main__":
    main()