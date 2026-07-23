# ============================================================
# main.py
# ============================================================
# FORMAT: Format 2 — Hands-Off Auto-Detection Pipeline
#
# PURPOSE:
# Entry point for the Format 2 hands-off pipeline. Identical
# pipeline order to Format 1 but passes DetectedConfig object
# through each step instead of manual period config.
#
# PIPELINE ORDER:
#   1. LOAD     — loads files, auto-detects format, runs
#                 detector.detect_all() to discover all
#                 period mappings from the file itself
#   2. VALIDATE — cross-checks MAT using auto-detected
#                 monthly columns and MAT column name
#   3. EXTRACT  — extracts values using auto-detected periods
#   4. WRITE    — populates template, logs growth using
#                 auto-detected period keys
#
# HOW TO RUN:
#   python main.py
#
# WHAT TO UPDATE BEFORE RUNNING (new month, same category):
#   - Drop new files into input/ folder
#   - Nothing else. Period names are auto-detected.
#
# WHAT TO UPDATE BEFORE RUNNING (new category):
#   - Update SOURCE_FILE, CATEGORY_NAME, TEMPLATE_SHEET
#   - Update brand role names
#   - Update geography mappings if different
#   - No period column names needed
# ============================================================

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loader      import load_source
from transformer import extract_data
from validation  import run_validations
from writer      import write_output
from config      import CATEGORY_NAME, OUTPUT_FILE


def main():
    print("\n" + "=" * 60)
    print(f"NIELSEN AUTOMATION (FORMAT 2) — STARTING")
    print(f"Category : {CATEGORY_NAME}")
    print(f"Output   : {OUTPUT_FILE}")
    print("=" * 60)

    # Step 1 — Load + Auto-detect
    df, detected = load_source()
    print(f"\nAuto-detection summary:")
    print(detected)

    # Step 2 — Validate
    run_validations(df, detected)

    # Step 3 — Extract
    data = extract_data(df, detected)

    # Step 4 — Write
    write_output(data, detected)

    print("\n" + "=" * 60)
    print(f"DONE. Output file is ready.")
    print(f"  {OUTPUT_FILE}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
