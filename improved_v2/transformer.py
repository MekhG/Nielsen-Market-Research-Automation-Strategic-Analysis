# ============================================================
# transformer.py
# ============================================================
# FORMAT: Format 2 — Hands-Off Auto-Detection Pipeline
#
# PURPOSE:
# This file extracts specific data values from the loaded
# DataFrame using the auto-detected period mappings from
# detector.py rather than manually configured period names.
#
# KEY DIFFERENCE FROM FORMAT 1:
#
# FORMAT 1 transformer.py:
#   Reads period column names from WIDE_PERIODS and
#   LONG_PERIODS dictionaries in config.py, which the
#   analyst manually updates each month.
#
# FORMAT 2 transformer.py:
#   Reads period column names from the DetectedConfig object
#   returned by detector.detect_all(). No manual period
#   configuration needed. The detected.periods dict contains
#   the same keys (Mth_CY, L3M_PY etc.) but the values are
#   auto-discovered from the file's column names.
#   L6M months are also taken from detected.l6m_months_cy
#   and detected.l6m_months_py instead of config.py lists.
#
# ALL OTHER BEHAVIOUR IS IDENTICAL TO FORMAT 1:
#   - Product == Segment rule for wide format row selection
#   - Brand Family + Product Name filter for long format
#   - Single row validation (warns if 0 or >1 rows found)
#   - L6M derivation (sum for additive, average for ratios)
#   - Same role/metric/geography iteration structure
#
# THIS FILE DOES NOT NEED TO BE EDITED BETWEEN RUNS.
# ============================================================

import pandas as pd
from config import (
    WIDE_COLS, LONG_COLS, METRIC_NAMES,
    WIDE_ROLES, LONG_ROLES,
    WIDE_GEO_MAP, LONG_GEO_MAP,
    L6M_SUM_METRICS, L6M_AVG_METRICS,
    BLOCK_STARTS,
)

ROLE_METRICS = {
    "focal"      : ["Sales Value", "Sales Units", "MS Val", "Store Count", "WD"],
    "category"   : ["Sales Value", "Sales Units", "Store Count"],
    "competitor" : ["Sales Value", "Sales Units", "MS Val", "Store Count", "WD"],
}


# =============================================================================
# L6M DERIVATION
# =============================================================================

def compute_l6m(row, months, metric_name):
    """
    Derives L6M by summing or averaging 6 monthly columns.
    Uses auto-detected month lists from DetectedConfig.
    """
    values = [row[m] for m in months
              if m in row.index and pd.notna(row[m])]
    if not values:
        return None
    if len(values) < 6:
        print(f"  WARNING: Only {len(values)}/6 months available for L6M")
    if metric_name in L6M_SUM_METRICS:
        return round(sum(values), 2)
    return round(sum(values) / len(values), 2)


# =============================================================================
# WIDE FORMAT EXTRACTION
# =============================================================================

def get_wide_value(df, detected, role_key, geo_label, metric_key, period_key):
    """
    Extracts a single value from a wide-format DataFrame.
    Uses detected.periods for period column lookup instead
    of manually configured WIDE_PERIODS from config.py.
    """
    source_geo = next(
        (src for src, tgt in WIDE_GEO_MAP.items() if tgt == geo_label), None
    )
    if source_geo is None:
        return None

    role        = WIDE_ROLES[role_key]
    metric_name = METRIC_NAMES[metric_key]
    period_col  = detected.periods.get(period_key)

    if period_col is None:
        return None  # Period not found in this file

    mask = (
        (df[WIDE_COLS["geography"]] == source_geo) &
        (df[WIDE_COLS["brand"]]     == role["brand"]) &
        (df[WIDE_COLS["level"]]     == role["level"]) &
        (df[WIDE_COLS["segment"]]   == role["segment"]) &
        (df[WIDE_COLS["measure"]]   == metric_name)
    )
    result = df[mask]

    if len(result) == 0:
        print(f"  WARNING: No row — {role_key}, {geo_label}, "
              f"{metric_key}, {period_key}")
        return None
    if len(result) > 1:
        print(f"  WARNING: Multiple rows — {role_key}, {geo_label}, "
              f"{metric_key}, {period_key}. Using first.")

    val = result.iloc[0][period_col]
    return round(float(val), 2) if pd.notna(val) else None


# =============================================================================
# LONG FORMAT EXTRACTION
# =============================================================================

def get_long_value(df, detected, role_key, geo_label, metric_key, period_key):
    """
    Extracts a single value from a long-format DataFrame.
    Uses detected.periods for pre-built period columns and
    detected.l6m_months_cy/py for L6M derivation instead
    of manually configured lists from config.py.
    """
    source_geo_key = next(
        (k for k, v in LONG_GEO_MAP.items() if v == geo_label), None
    )
    if source_geo_key is None:
        return None

    role        = LONG_ROLES[role_key]
    metric_name = METRIC_NAMES[metric_key]

    mask = (
        (df["geo_key"]                    == source_geo_key) &
        (df[LONG_COLS["brand_family"]]    == role["brand_family"]) &
        (df[LONG_COLS["product_name"]]    == role["product_name"]) &
        (df[LONG_COLS["metric"]]          == metric_name)
    )
    result = df[mask]

    if len(result) == 0:
        print(f"  WARNING: No row — {role_key}, {geo_label}, "
              f"{metric_key}, {period_key}")
        return None
    if len(result) > 1:
        print(f"  WARNING: Multiple rows — {role_key}, {geo_label}, "
              f"{metric_key}, {period_key}. Using first.")

    row = result.iloc[0]

    # L6M uses auto-detected monthly columns
    if period_key == "L6M_CY":
        return compute_l6m(row, detected.l6m_months_cy, metric_name)
    if period_key == "L6M_PY":
        return compute_l6m(row, detected.l6m_months_py, metric_name)

    # All other periods use auto-detected column names
    period_col = detected.periods.get(period_key)
    if period_col is None:
        return None

    val = row[period_col]
    return round(float(val), 2) if pd.notna(val) else None


# =============================================================================
# MAIN EXTRACTION FUNCTION
# =============================================================================

def extract_data(df, detected):
    """
    Extracts all values using auto-detected period configuration.

    Args:
        df       : loaded DataFrame
        detected : DetectedConfig object from detector.detect_all()

    Returns:
        dict keyed by (role, geo_label, metric_key, period_key) -> value
    """
    print(f"\nExtracting data ({detected.fmt} format)...")

    data    = {}
    geos    = (list(WIDE_GEO_MAP.values()) if detected.fmt == "wide"
               else list(LONG_GEO_MAP.values()))
    periods = list(detected.periods.keys())

    # Add L6M periods for long format
    if detected.fmt == "long":
        if detected.l6m_months_cy:
            periods += ["L6M_CY"]
        if detected.l6m_months_py:
            periods += ["L6M_PY"]

    for role_key, metrics in ROLE_METRICS.items():
        for geo_label in geos:
            for metric_key in metrics:
                if (role_key, metric_key) not in BLOCK_STARTS:
                    continue
                for period_key in periods:
                    if detected.fmt == "wide":
                        val = get_wide_value(
                            df, detected, role_key,
                            geo_label, metric_key, period_key
                        )
                    else:
                        val = get_long_value(
                            df, detected, role_key,
                            geo_label, metric_key, period_key
                        )
                    data[(role_key, geo_label, metric_key, period_key)] = val

    print(f"  Extraction complete: {len(data)} values extracted")
    return data
