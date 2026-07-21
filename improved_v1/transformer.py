# ============================================================
# transformer.py
# ============================================================
# FORMAT: Format 1 — Single Category, Config-Driven Pipeline
#
# PURPOSE:
# This file extracts specific data values from the loaded
# DataFrame and organises them into a structured dictionary
# keyed by (role, geography, metric, period). This dictionary
# is then passed to writer.py to populate the output template.
#
# The transformer handles two file formats differently:
#
# WIDE FORMAT EXTRACTION:
# Applies a three-part filter to isolate exactly one row per
# brand x geography x metric combination:
#   - Product == role["brand"]
#   - Level == role["level"]
#   - Segment == role["segment"]  (the Product == Segment rule)
# The Product == Segment rule is the structural rule in Nielsen
# wide exports that identifies the brand-level total row, as
# opposed to segment or variant rows (e.g. Menthol, Orange).
# All period values are read directly from pre-built columns.
#
# LONG FORMAT EXTRACTION:
# Filters by Brand Family, Product Name, geo_key and Metric
# to isolate exactly one row per combination.
# Pre-built period columns are read directly (Mth, L3M, YTD, MAT).
# L6M is NOT pre-built in long format files and is DERIVED by
# summing or averaging the 6 most recent monthly columns:
#   - Sales Value and Units: SUM (additive flows)
#   - MS Val%, Store Count, WD%: AVERAGE (ratios/snapshots)
#
# VALIDATION:
# For every filter applied, the transformer checks that exactly
# one row is returned. If zero rows are found, a WARNING is
# printed (geography may not exist in this file). If more than
# one row is found, a WARNING is printed to flag potential
# double-counting. Neither case silently produces wrong output.
#
# THIS FILE DOES NOT NEED TO BE EDITED BETWEEN RUNS.
# All brand names, column names and period names are read from
# config.py.
# ============================================================

import pandas as pd
from config import (
    WIDE_COLS, LONG_COLS, METRIC_NAMES,
    WIDE_PERIODS, LONG_PERIODS,
    WIDE_ROLES, LONG_ROLES,
    WIDE_GEO_MAP, LONG_GEO_MAP,
    L6M_MONTHS_CY, L6M_MONTHS_PY,
    L6M_SUM_METRICS, L6M_AVG_METRICS,
    BLOCK_STARTS,
)


# =============================================================================
# METRICS AND ROLES
# =============================================================================

ROLE_METRICS = {
    "focal"      : ["Sales Value", "Sales Units", "MS Val", "Store Count", "WD"],
    "category"   : ["Sales Value", "Sales Units", "Store Count"],
    "competitor" : ["Sales Value", "Sales Units", "MS Val", "Store Count", "WD"],
}


# =============================================================================
# L6M DERIVATION (LONG FORMAT ONLY)
# =============================================================================

def compute_l6m(row, months, metric_name):
    """
    Derives L6M value by summing or averaging 6 monthly columns.
    Additive metrics (Value, Units) are summed.
    Non-additive metrics (MS%, Store Count, WD%) are averaged.
    Skips missing months gracefully with a warning.
    """
    values = [row[m] for m in months if m in row.index and pd.notna(row[m])]
    if len(values) == 0:
        return None
    if len(values) < 6:
        print(f"  WARNING: Only {len(values)}/6 months available for L6M derivation")
    if metric_name in L6M_SUM_METRICS:
        return round(sum(values), 2)
    else:
        return round(sum(values) / len(values), 2)


# =============================================================================
# WIDE FORMAT EXTRACTION
# =============================================================================

def get_wide_value(df, role_key, geo_label, metric_key, period_key):
    """
    Extracts a single value from a wide-format DataFrame.
    Returns None if the geography is not in the file (expected gap).
    Prints WARNING if 0 or >1 rows found for other reasons.
    """
    # Reverse-lookup source geography from template label
    source_geo = next(
        (src for src, tgt in WIDE_GEO_MAP.items() if tgt == geo_label), None
    )
    if source_geo is None:
        return None  # Geography not in this file — expected for some categories

    role        = WIDE_ROLES[role_key]
    metric_name = METRIC_NAMES[metric_key]
    period_col  = WIDE_PERIODS[period_key]

    mask = (
        (df[WIDE_COLS["geography"]] == source_geo) &
        (df[WIDE_COLS["brand"]]     == role["brand"]) &
        (df[WIDE_COLS["level"]]     == role["level"]) &
        (df[WIDE_COLS["segment"]]   == role["segment"]) &
        (df[WIDE_COLS["measure"]]   == metric_name)
    )
    result = df[mask]

    if len(result) == 0:
        print(f"  WARNING: No row — role={role_key}, geo={geo_label}, "
              f"metric={metric_key}, period={period_key}")
        return None
    if len(result) > 1:
        print(f"  WARNING: Multiple rows — role={role_key}, geo={geo_label}, "
              f"metric={metric_key}, period={period_key}. Using first row.")

    val = result.iloc[0][period_col]
    return round(float(val), 2) if pd.notna(val) else None


# =============================================================================
# LONG FORMAT EXTRACTION
# =============================================================================

def get_long_value(df, role_key, geo_label, metric_key, period_key):
    """
    Extracts a single value from a long-format DataFrame.
    Handles pre-built periods by direct column read.
    Handles L6M by deriving from 6 monthly columns.
    Returns None if geography not in file or value missing.
    """
    # Reverse-lookup geo_key from template label
    source_geo_key = next(
        (k for k, v in LONG_GEO_MAP.items() if v == geo_label), None
    )
    if source_geo_key is None:
        return None

    role        = LONG_ROLES[role_key]
    metric_name = METRIC_NAMES[metric_key]

    mask = (
        (df["geo_key"]                             == source_geo_key) &
        (df[LONG_COLS["brand_family"]]             == role["brand_family"]) &
        (df[LONG_COLS["product_name"]]             == role["product_name"]) &
        (df[LONG_COLS["metric"]]                   == metric_name)
    )
    result = df[mask]

    if len(result) == 0:
        print(f"  WARNING: No row — role={role_key}, geo={geo_label}, "
              f"metric={metric_key}, period={period_key}")
        return None
    if len(result) > 1:
        print(f"  WARNING: Multiple rows — role={role_key}, geo={geo_label}, "
              f"metric={metric_key}, period={period_key}. Using first row.")

    row = result.iloc[0]

    # L6M requires derivation
    if period_key == "L6M_CY":
        return compute_l6m(row, L6M_MONTHS_CY, metric_name)
    elif period_key == "L6M_PY":
        return compute_l6m(row, L6M_MONTHS_PY, metric_name)

    # All other periods: direct read from pre-built column
    period_col = LONG_PERIODS.get(period_key)
    if period_col is None:
        print(f"  WARNING: Period {period_key} not in LONG_PERIODS config")
        return None

    val = row[period_col]
    return round(float(val), 2) if pd.notna(val) else None


# =============================================================================
# MAIN EXTRACTION FUNCTION
# =============================================================================

def extract_data(df, fmt):
    """
    Extracts all values from the loaded DataFrame into a dictionary.
    Automatically routes to wide or long extraction based on fmt.

    Returns:
        dict keyed by (role, geo_label, metric_key, period_key) -> value
    """
    print(f"\nExtracting data ({fmt} format)...")

    data    = {}
    geos    = list(WIDE_GEO_MAP.values()) if fmt == "wide" else list(LONG_GEO_MAP.values())
    periods = (list(WIDE_PERIODS.keys()) if fmt == "wide"
               else list(LONG_PERIODS.keys()) + ["L6M_CY", "L6M_PY"])

    for role_key, metrics in ROLE_METRICS.items():
        for geo_label in geos:
            for metric_key in metrics:
                # Skip metric blocks not in template
                if (role_key, metric_key) not in BLOCK_STARTS:
                    continue
                for period_key in periods:
                    if fmt == "wide":
                        val = get_wide_value(df, role_key, geo_label, metric_key, period_key)
                    else:
                        val = get_long_value(df, role_key, geo_label, metric_key, period_key)
                    data[(role_key, geo_label, metric_key, period_key)] = val

    print(f"  Extraction complete: {len(data)} values extracted")
    return data
