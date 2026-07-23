# ============================================================
# validation.py
# ============================================================
# FORMAT: Format 2 — Hands-Off Auto-Detection Pipeline
#
# PURPOSE:
# Identical in purpose to Format 1 validation.py — cross-checks
# the pre-built MAT column against the sum of 12 monthly columns.
#
# KEY DIFFERENCE FROM FORMAT 1:
#
# FORMAT 1 validation.py:
#   Uses manually configured period column names from config.py
#   (LONG_PERIODS["MAT_CY"]) and a hardcoded list of 12 months.
#
# FORMAT 2 validation.py:
#   Uses auto-detected period column names from DetectedConfig
#   (detected.periods["MAT_CY"]) and the auto-detected list of
#   all monthly columns (detected.all_monthly) to derive the
#   12-month window for cross-validation. No hardcoded months.
#
# THIS FILE DOES NOT NEED TO BE EDITED BETWEEN RUNS.
# ============================================================

import pandas as pd
from config import LONG_COLS, LONG_ROLES, LONG_GEO_MAP, METRIC_NAMES


def validate_mat_long(df, detected):
    """
    Cross-checks the auto-detected MAT_CY column against the
    sum of the 12 most recent monthly columns.
    Uses detected.all_monthly and detected.periods["MAT_CY"].
    Validates within 1% tolerance for rounding differences.
    """
    print("\n" + "=" * 60)
    print("RUNNING MAT CROSS-VALIDATION (Long Format)")
    print("=" * 60)

    mat_col_cy = detected.periods.get("MAT_CY")
    if not mat_col_cy:
        print("  WARNING: MAT_CY period not detected. Skipping validation.")
        print("=" * 60)
        return

    if len(detected.all_monthly) < 12:
        print(f"  WARNING: Only {len(detected.all_monthly)} monthly columns found."
              f" Need 12 for MAT validation. Skipping.")
        print("=" * 60)
        return

    last_12     = detected.all_monthly[-12:]
    metric_name = METRIC_NAMES["Sales Value"]

    # Validate at All India level for all roles
    all_india_key = next(
        (k for k, v in LONG_GEO_MAP.items() if v == "All India (Total)"), None
    )
    if not all_india_key:
        print("  WARNING: All India geo_key not found. Skipping.")
        print("=" * 60)
        return

    checks = [
        (LONG_ROLES[r]["brand_family"],
         LONG_ROLES[r]["product_name"], r)
        for r in ["focal", "category", "competitor"]
    ]

    passed = 0
    failed = 0

    for brand_family, product_name, role_key in checks:
        mask = (
            (df["geo_key"]                 == all_india_key) &
            (df[LONG_COLS["brand_family"]] == brand_family) &
            (df[LONG_COLS["product_name"]] == product_name) &
            (df[LONG_COLS["metric"]]       == metric_name)
        )
        result = df[mask]
        if result.empty:
            print(f"  SKIP: No data for {role_key} ({brand_family})")
            continue

        row          = result.iloc[0]
        derived_mat  = round(
            sum(row[m] for m in last_12 if pd.notna(row.get(m))), 2
        )
        reported_mat = row[mat_col_cy]

        if not reported_mat or pd.isna(reported_mat):
            print(f"  SKIP: Zero/null MAT for {role_key}")
            continue

        diff_pct = abs(derived_mat - reported_mat) / abs(reported_mat) * 100

        if diff_pct > 1:
            print(f"  ⚠ MISMATCH — {role_key} ({brand_family}) All India:")
            print(f"    Derived  : {derived_mat:.2f}")
            print(f"    Reported : {reported_mat:.2f}")
            print(f"    Diff     : {diff_pct:.1f}%")
            failed += 1
        else:
            print(f"  ✓ PASS — {role_key} ({brand_family}) "
                  f"(diff: {diff_pct:.2f}%)")
            passed += 1

    print(f"\n  Summary: {passed} passed, {failed} mismatches")
    print("=" * 60)


def run_validations(df, detected):
    """
    Runs applicable validations using auto-detected config.
    MAT validation runs for long format only.
    """
    if detected.fmt == "long":
        validate_mat_long(df, detected)
    else:
        print("\n  MAT validation: skipped (wide format — periods pre-built)")
