## Validation (validation.py)
##Cross-checks the pre-built MAT column against the sum of 12 individual monthly columns for key
## brand and geography combinations. Validates within a 1% tolerance to allow for rounding. Any
## mismatch is printed with the derived value, reported value and percentage difference.

%%writefile /content/nielsen/validation.py
import sys
sys.path.append("/content/nielsen")

import pandas as pd
from config import SANITIZER_COLS

def validate_mat(df, brand_family, geo_key):
    """
    MAT should equal sum of 12 monthly columns.
    Checks within 1% tolerance to allow for rounding.
    """
    mask = (
        (df["geo_key"]                      == geo_key) &
        (df[SANITIZER_COLS["brand_family"]] == brand_family) &
        (df[SANITIZER_COLS["product_name"]] == "Total") &
        (df[SANITIZER_COLS["metric"]]       == "Sales Value in Cr.")
    )

    if df[mask].empty:
        print(f"  WARNING: No data found for {brand_family} {geo_key}")
        return

    row = df[mask].iloc[0]

    # Last 12 months
    monthly_cols = [
        "May 2025", "Jun 2025", "Jul 2025", "Aug 2025",
        "Sep 2025", "Oct 2025", "Nov 2025", "Dec 2025",
        "Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026"
    ]

    # Check all monthly columns exist
    missing = [m for m in monthly_cols if m not in df.columns]
    if missing:
        print(f"  WARNING: Missing monthly columns for MAT check: {missing}")
        return

    derived_mat  = sum(row[m] for m in monthly_cols)
    reported_mat = row["MAT Apr 2026"]

    diff = abs(derived_mat - reported_mat)
    pct  = (diff / reported_mat) * 100 if reported_mat != 0 else 0

    if pct > 1:
        print(f"  WARNING: MAT mismatch for {brand_family} {geo_key}")
        print(f"    Derived from monthly cols : {derived_mat:.2f}")
        print(f"    Reported MAT column       : {reported_mat:.2f}")
        print(f"    Difference                : {diff:.2f} ({pct:.1f}%)")
    else:
        print(f"  MAT validated for {brand_family} {geo_key} "
              f"— within 1% tolerance ✅")


def run_all_validations(df_san):
    """
    Runs MAT validation for key brand × geography combinations.
    """
    print("\n" + "="*60)
    print("RUNNING VALIDATIONS")
    print("="*60)

    checks = [
        ("DETTOL",   ("ALL INDIA", "Total", "Total")),
        ("LIFEBUOY", ("ALL INDIA", "Total", "Total")),
        ("Total",    ("ALL INDIA", "Total", "Total")),
        ("DETTOL",   ("Zone", "North", "Total")),
        ("DETTOL",   ("Zone", "South", "Total")),
    ]

    for brand, geo in checks:
        validate_mat(df_san, brand, geo)

    print("="*60 + "\n")
