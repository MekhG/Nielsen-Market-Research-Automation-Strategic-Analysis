# ============================================================
# validation.py
# ============================================================
# FORMAT: Format 1 — Single Category, Config-Driven Pipeline
#
# PURPOSE:
# This file performs cross-validation checks on the loaded
# data before the output is written. It is designed to catch
# data quality issues early — before wrong numbers silently
# land in the output file.
#
# WHAT IT CHECKS:
#
# 1. MAT CROSS-VALIDATION (Long format only):
#    The pre-built MAT column in the Sanitizer-style file is
#    cross-checked against the sum of 12 individual monthly
#    columns for key brand and geography combinations.
#    Validated within 1% tolerance to allow for rounding.
#    Any mismatch is printed with:
#      - The derived value (sum of 12 months)
#      - The reported value (pre-built MAT column)
#      - The percentage difference
#    This helps the analyst decide whether to investigate
#    the source file before accepting the output.
#
# 2. COLUMN EXISTENCE CHECK (called from loader.py):
#    Ensures all expected columns are present before any
#    data is read. This is the first line of defence against
#    renamed or restructured source files.
#
# WHAT IT DOES NOT CHECK:
#    - Wide format MAT values (pre-built and trusted from agency)
#    - Individual cell value accuracy (spot checks are manual)
#    - Market share values exceeding 100% (treated as index values)
#
# THIS FILE DOES NOT NEED TO BE EDITED BETWEEN RUNS.
# The list of brand/geography combinations to validate is
# derived automatically from the config.
# ============================================================

import pandas as pd
from config import (
    LONG_COLS, LONG_PERIODS,
    LONG_ROLES, LONG_GEO_MAP,
    METRIC_NAMES,
)


def validate_mat_long(df):
    """
    Cross-checks the pre-built MAT column against the sum of
    12 individual monthly columns for key brand x geography
    combinations in long-format files.

    Validates within 1% tolerance to allow for rounding.
    Prints result for each combination checked.
    """
    print("\n" + "=" * 60)
    print("RUNNING MAT CROSS-VALIDATION (Long Format)")
    print("=" * 60)

    # Identify the 12 monthly columns preceding the latest MAT
    # These are all columns that look like "Mon YYYY" (3-letter month + 4-digit year)
    import re
    monthly_pattern = re.compile(r'^[A-Z][a-z]{2} \d{4}$')
    monthly_cols = [c for c in df.columns if monthly_pattern.match(str(c))]

    if len(monthly_cols) < 12:
        print(f"  WARNING: Only {len(monthly_cols)} monthly columns found."
              f" Need at least 12 for MAT validation. Skipping.")
        print("=" * 60)
        return

    # Use the last 12 monthly columns (most recent MAT window)
    last_12 = monthly_cols[-12:]
    mat_col_cy = LONG_PERIODS.get("MAT_CY")

    if mat_col_cy not in df.columns:
        print(f"  WARNING: MAT column '{mat_col_cy}' not found. Skipping validation.")
        print("=" * 60)
        return

    metric_name = METRIC_NAMES["Sales Value"]

    # Validate for focal brand and category at All India level
    checks = []
    all_india_key = next(
        (k for k, v in LONG_GEO_MAP.items() if v == "All India (Total)"), None
    )
    if all_india_key:
        for role_key in ["focal", "category", "competitor"]:
            role = LONG_ROLES.get(role_key)
            if role:
                checks.append((
                    role["brand_family"],
                    role["product_name"],
                    all_india_key,
                    role_key
                ))

    passed = 0
    failed = 0

    for brand_family, product_name, geo_key, role_key in checks:
        mask = (
            (df["geo_key"]                   == geo_key) &
            (df[LONG_COLS["brand_family"]]   == brand_family) &
            (df[LONG_COLS["product_name"]]   == product_name) &
            (df[LONG_COLS["metric"]]         == metric_name)
        )
        result = df[mask]

        if result.empty:
            print(f"  SKIP: No data for {role_key} ({brand_family}) at All India")
            continue

        row          = result.iloc[0]
        derived_mat  = round(sum(row[m] for m in last_12 if pd.notna(row.get(m, None))), 2)
        reported_mat = row[mat_col_cy]

        if reported_mat == 0 or pd.isna(reported_mat):
            print(f"  SKIP: Zero/null MAT for {role_key} ({brand_family})")
            continue

        diff_pct = abs(derived_mat - reported_mat) / abs(reported_mat) * 100

        if diff_pct > 1:
            print(f"  ⚠ MISMATCH — {role_key} ({brand_family}) All India:")
            print(f"    Derived from 12 months : {derived_mat:.2f}")
            print(f"    Reported MAT column    : {reported_mat:.2f}")
            print(f"    Difference             : {diff_pct:.1f}%")
            failed += 1
        else:
            print(f"  ✓ PASS — {role_key} ({brand_family}) All India "
                  f"(diff: {diff_pct:.2f}%)")
            passed += 1

    print(f"\n  Summary: {passed} passed, {failed} mismatches")
    print("=" * 60)


def run_validations(df, fmt):
    """
    Runs all applicable validations for the loaded DataFrame.
    MAT cross-validation only runs for long-format files since
    wide-format files have pre-built periods trusted from agency.
    """
    if fmt == "long":
        validate_mat_long(df)
    else:
        print("\n  MAT cross-validation: skipped (wide format — periods pre-built)")
