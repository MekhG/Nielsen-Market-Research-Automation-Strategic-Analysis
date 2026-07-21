# ============================================================
# main.py
# ============================================================
# FORMAT: Format 1 — Single Category, Config-Driven Pipeline
#
# PURPOSE:
# This is the entry point for the Nielsen Market Research
# Automation Pipeline. It orchestrates the full pipeline
# from loading raw source files to producing the populated
# output Excel file.
#
# PIPELINE ORDER:
#   1. LOAD    — loader.py reads and validates source files,
#                auto-detects format (wide or long),
#                merges two files if HAS_SECOND_FILE = True
#   2. VALIDATE— validation.py cross-checks MAT values
#                against monthly columns (long format only)
#   3. EXTRACT — transformer.py extracts all values into a
#                structured dictionary
#   4. WRITE   — writer.py copies the template and populates
#                it with extracted values, logs growth figures
#
# HOW TO RUN:
#   python main.py
#
# WHAT TO UPDATE BEFORE RUNNING:
#   - config.py only — file paths, brand names, period names
#   - No other file needs to be touched
#
# OUTPUT:
#   Output_{CategoryName}.xlsx in the output/ folder
#   (CategoryName is set by CATEGORY_NAME in config.py)
#
# NOTE ON ERRORS:
#   The pipeline fails loudly with a clear error message if:
#   - A required column is missing from the source file
#   - The template sheet name is not found
#   - The source files have incompatible structures
#   This is intentional — silent wrong output is worse than
#   a clear error that tells you exactly what to fix.
# ============================================================

import sys
import os

# Ensure the script can find all modules when run from any directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loader      import load_source
from transformer import extract_data
from validation  import run_validations
from writer      import write_output
from config      import CATEGORY_NAME, OUTPUT_FILE


def main():
    print("\n" + "=" * 60)
    print(f"NIELSEN AUTOMATION — STARTING")
    print(f"Category : {CATEGORY_NAME}")
    print(f"Output   : {OUTPUT_FILE}")
    print("=" * 60)

    # Step 1 — Load
    df, fmt = load_source()

    # Step 2 — Validate
    run_validations(df, fmt)

    # Step 3 — Extract
    data = extract_data(df, fmt)

    # Step 4 — Write
    write_output(data, fmt)

    print("\n" + "=" * 60)
    print(f"DONE. Output file is ready.")
    print(f"  {OUTPUT_FILE}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
