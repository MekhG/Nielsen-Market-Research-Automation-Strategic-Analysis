## Data Transformation (transformer.py)
## Extracts specific values from the loaded DataFrames based on predefined roles, geographies, metrics
## and time periods. Applies the Product == Segment structural rule to isolate the correct brand-level
## row in the Lozenge file. Derives L6M values for the Sanitizer file — summing monthly columns for
## additive metrics and averaging for non-additive metrics.

%%writefile /content/nielsen/transformer.py
import sys
sys.path.append("/content/nielsen")

import pandas as pd
from config import (
    LOZENGE_COLS, LOZENGE_METRIC_NAMES, LOZENGE_PERIODS, LOZENGE_ROLES, LOZENGE_GEO_MAP,
    SANITIZER_COLS, SANITIZER_METRIC_NAMES, SANITIZER_PERIODS, SANITIZER_ROLES,
    SANITIZER_GEO_MAP, L6M_MONTHS_CY, L6M_MONTHS_PY,
    L6M_SUM_METRICS, L6M_AVG_METRICS
)


# =============================================================================
# LOZENGE EXTRACTION
# =============================================================================

def get_lozenge_value(df, role_key, geo_label, metric_key, period_key):
    """
    Extracts a single value from the Lozenge DataFrame.

    Args:
        df         : Lozenge DataFrame
        role_key   : "focal", "category", or "competitor"
        geo_label  : template geography label e.g. "All India (Total)"
        metric_key : "Sales Value", "Sales Units", "MS Val", "Store Count", "WD"
        period_key : "Mth_CY", "L3M_PY", etc.

    Returns:
        float value or None if not available
    """
    # Get source geography value from reverse map
    source_geo = None
    for src, tgt in LOZENGE_GEO_MAP.items():
        if tgt == geo_label:
            source_geo = src
            break

    # Geography not in Lozenge file — return None
    if source_geo is None:
        return None

    # Get role definition
    role = LOZENGE_ROLES[role_key]
    metric_name = LOZENGE_METRIC_NAMES[metric_key]
    period_col  = LOZENGE_PERIODS[period_key]

    # Filter rows
    mask = (
        (df[LOZENGE_COLS["geography"]] == source_geo) &
        (df[LOZENGE_COLS["brand"]]     == role["brand"]) &
        (df[LOZENGE_COLS["level"]]     == role["level"]) &
        (df[LOZENGE_COLS["segment"]]   == role["segment"]) &
        (df[LOZENGE_COLS["measure"]]   == metric_name)
    )

    result = df[mask]

    # Validation
    if len(result) == 0:
        print(f"  WARNING: No row found — role={role_key}, geo={geo_label}, "
              f"metric={metric_key}, period={period_key}")
        return None
    if len(result) > 1:
        print(f"  WARNING: Multiple rows found — role={role_key}, geo={geo_label}, "
              f"metric={metric_key}, period={period_key}. Using first row.")

    return result.iloc[0][period_col]


def extract_lozenge_data(df):
    """
    Extracts all values from the Lozenge file into a nested dictionary.

    Returns:
        dict keyed by (role, geo_label, metric_key, period_key) → value
    """
    print("Extracting Lozenge data...")

    data = {}

    roles   = list(LOZENGE_ROLES.keys())
    geos    = list(LOZENGE_GEO_MAP.values())
    periods = list(LOZENGE_PERIODS.keys())

    # Metrics per role
    role_metrics = {
        "focal"      : ["Sales Value", "Sales Units", "MS Val", "Store Count", "WD"],
        "category"   : ["Sales Value", "Sales Units", "Store Count"],
        "competitor" : ["Sales Value", "Sales Units", "MS Val", "Store Count", "WD"],
    }

    for role_key in roles:
        for geo_label in geos:
            for metric_key in role_metrics[role_key]:
                for period_key in periods:
                    val = get_lozenge_value(
                        df, role_key, geo_label, metric_key, period_key
                    )
                    data[(role_key, geo_label, metric_key, period_key)] = val

    print(f"  Lozenge extraction complete: {len(data)} values extracted")
    return data


# =============================================================================
# SANITIZER EXTRACTION
# =============================================================================

def _compute_l6m(row, months, metric_name):
    """
    Derives L6M value by summing or averaging 6 monthly columns.
    Additive metrics (Value, Units) are summed.
    Non-additive metrics (MS%, Store Count, WD%) are averaged.
    """
    values = [row[m] for m in months if m in row.index and pd.notna(row[m])]

    if len(values) == 0:
        return None

    if metric_name in L6M_SUM_METRICS:
        return sum(values)
    else:
        return sum(values) / len(values)


def get_sanitizer_value(df, role_key, geo_label, metric_key, period_key):
    """
    Extracts a single value from the combined Sanitizer DataFrame.

    Args:
        df         : Combined Sanitizer DataFrame
        role_key   : "focal", "category", or "competitor"
        geo_label  : template geography label e.g. "All India (Total)"
        metric_key : "Sales Value", "Sales Units", "MS Val", "Store Count", "WD"
        period_key : "Mth_CY", "L3M_PY", etc.

    Returns:
        float value or None if not available
    """
    # Get source geo_key from reverse map
    source_geo_key = None
    for key, label in SANITIZER_GEO_MAP.items():
        if label == geo_label:
            source_geo_key = key
            break

    if source_geo_key is None:
        return None

    # Get role and metric definitions
    role        = SANITIZER_ROLES[role_key]
    metric_name = SANITIZER_METRIC_NAMES[metric_key]

    # Filter rows
    mask = (
        (df["geo_key"]                            == source_geo_key) &
        (df[SANITIZER_COLS["brand_family"]]       == role["brand_family"]) &
        (df[SANITIZER_COLS["product_name"]]       == role["product_name"]) &
        (df[SANITIZER_COLS["metric"]]             == metric_name)
    )

    result = df[mask]

    # Validation
    if len(result) == 0:
        print(f"  WARNING: No row found — role={role_key}, geo={geo_label}, "
              f"metric={metric_key}, period={period_key}")
        return None
    if len(result) > 1:
        print(f"  WARNING: Multiple rows found — role={role_key}, geo={geo_label}, "
              f"metric={metric_key}, period={period_key}. Using first row.")

    row = result.iloc[0]

    # L6M requires derivation from monthly columns
    if period_key == "L6M_CY":
        return _compute_l6m(row, L6M_MONTHS_CY, metric_name)
    elif period_key == "L6M_PY":
        return _compute_l6m(row, L6M_MONTHS_PY, metric_name)

    # All other periods use pre-built columns
    period_col = SANITIZER_PERIODS[period_key]
    return row[period_col]


def extract_sanitizer_data(df):
    """
    Extracts all values from the combined Sanitizer file
    into a nested dictionary.

    Returns:
        dict keyed by (role, geo_label, metric_key, period_key) → value
    """
    print("Extracting Sanitizer data...")

    data = {}

    roles   = list(SANITIZER_ROLES.keys())
    geos    = list(SANITIZER_GEO_MAP.values())
    periods = list(SANITIZER_PERIODS.keys()) + ["L6M_CY", "L6M_PY"]

    # Metrics per role
    role_metrics = {
        "focal"      : ["Sales Value", "Sales Units", "MS Val", "Store Count", "WD"],
        "category"   : ["Sales Value", "Sales Units", "Store Count"],
        "competitor" : ["Sales Value", "Sales Units", "MS Val", "Store Count", "WD"],
    }

    for role_key in roles:
        for geo_label in geos:
            for metric_key in role_metrics[role_key]:
                for period_key in periods:
                    val = get_sanitizer_value(
                        df, role_key, geo_label, metric_key, period_key
                    )
                    data[(role_key, geo_label, metric_key, period_key)] = val

    print(f"  Sanitizer extraction complete: {len(data)} values extracted")
    return data
