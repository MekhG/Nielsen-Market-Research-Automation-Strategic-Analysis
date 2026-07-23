# ============================================================
# detector.py
# ============================================================
# FORMAT: Format 2 — Hands-Off Auto-Detection Pipeline
#
# PURPOSE:
# This is the core auto-detection module that makes Format 2
# hands-off. It analyses the loaded DataFrame and automatically
# discovers all period-related information that Format 1
# requires the analyst to manually configure each month.
#
# WHAT IT AUTO-DETECTS:
#
# 1. FILE FORMAT (wide vs long):
#    Checks if a Metric column exists. If yes — long format.
#    If no — wide format. Same logic as Format 1 loader.
#
# 2. LATEST MONTH (for long format dated columns):
#    Scans all column names for patterns matching month-year
#    format (e.g. "Apr 2026", "Nov 2025"). Identifies the
#    most recent month as the current year latest month.
#    One year prior is automatically set as prior year.
#    Example: finds "Apr 2026" -> Mth_CY = "Apr 2026",
#             Mth_PY = "Apr 2025"
#
# 3. PRE-BUILT PERIOD COLUMNS (for long format):
#    Scans column names for patterns matching:
#      - "L3M {month} {year}"  -> L3M_CY and L3M_PY
#      - "YTD {month} {year}"  -> YTD_CY and YTD_PY
#      - "MAT {month} {year}"  -> MAT_CY and MAT_PY
#    Automatically assigns CY (most recent year) and
#    PY (one year prior) for each period type.
#
# 4. L6M MONTHLY COLUMNS (for long format):
#    Identifies all monthly columns in the file.
#    Takes the 6 most recent as L6M_CY months.
#    Takes the same 6 months one year prior as L6M_PY months.
#
# 5. WIDE FORMAT PERIODS (simple labels like "Mth 25"):
#    Scans for columns matching "Mth {YY}", "L3M {YY}" etc.
#    Assigns the higher year as CY and lower as PY.
#    No date parsing needed — purely label-based.
#
# WHAT IT DOES NOT AUTO-DETECT:
#    - Brand names (business decision — stays in config.py)
#    - Geography mappings (stays in config.py)
#    - Template sheet name (stays in config.py)
#    - Block start columns (stays in config.py)
#
# OUTPUT:
#    Returns a DetectedConfig object containing all auto-
#    detected period mappings, ready for use by transformer.py
#    and validation.py without any manual configuration.
#
# THIS FILE DOES NOT NEED TO BE EDITED BETWEEN RUNS.
# ============================================================

import re
import pandas as pd
from datetime import datetime
from config import LONG_COLS, L6M_SUM_METRICS, L6M_AVG_METRICS


# Month name to number mapping for date parsing
MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}

# Reverse mapping: month number to abbreviation
MONTH_ABBR = {v: k for k, v in MONTH_MAP.items()}


class DetectedConfig:
    """
    Holds all auto-detected period configuration.
    Passed to transformer.py and validation.py instead of
    the manual period dictionaries in config.py.
    """
    def __init__(self):
        self.fmt            = None    # "wide" or "long"
        self.latest_month   = None    # e.g. "Apr 2026"
        self.prior_month    = None    # e.g. "Apr 2025"
        self.periods        = {}      # period_key -> column name
        self.l6m_months_cy  = []      # list of 6 CY monthly column names
        self.l6m_months_py  = []      # list of 6 PY monthly column names
        self.all_monthly    = []      # all monthly column names found

    def __str__(self):
        lines = [
            f"  Format         : {self.fmt}",
            f"  Latest month   : {self.latest_month}",
            f"  Prior month    : {self.prior_month}",
            f"  Periods found  : {self.periods}",
            f"  L6M CY months  : {self.l6m_months_cy}",
            f"  L6M PY months  : {self.l6m_months_py}",
        ]
        return "\n".join(lines)


# =============================================================================
# FORMAT DETECTION
# =============================================================================

def detect_format(df):
    """
    Detects wide or long format by checking for Metric column.
    Wide: metrics are separate columns (e.g. Lozenge-style)
    Long: metrics stacked in single Metric column (e.g. Sanitizer-style)
    """
    metric_col = LONG_COLS["metric"]
    fmt = "long" if metric_col in df.columns else "wide"
    print(f"  Format detected: {fmt.upper()}")
    return fmt


# =============================================================================
# WIDE FORMAT PERIOD DETECTION
# =============================================================================

def detect_wide_periods(df):
    """
    Detects period columns in wide-format files.
    Wide files use simple labels like "Mth 25", "L3M 26" etc.
    Finds the two year suffixes and assigns higher as CY, lower as PY.

    Returns dict of period_key -> column name.
    """
    cols = df.columns.tolist()

    # Patterns to look for
    period_prefixes = ["Mth", "L3M", "L6M", "YTD", "MAT"]
    period_map = {}

    # Find all years present across period columns
    years_found = set()
    for col in cols:
        for prefix in period_prefixes:
            match = re.match(rf'^{prefix}\s+(\d{{2}})$', str(col))
            if match:
                years_found.add(int(match.group(1)))

    if len(years_found) < 2:
        print(f"  WARNING: Could not find two year suffixes in wide columns.")
        print(f"  Found years: {years_found}")
        return {}

    sorted_years = sorted(years_found)
    py_suffix = str(sorted_years[-2])  # lower year = prior year
    cy_suffix = str(sorted_years[-1])  # higher year = current year

    print(f"  Wide format years detected: PY={py_suffix}, CY={cy_suffix}")

    for prefix in period_prefixes:
        py_col = f"{prefix} {py_suffix}"
        cy_col = f"{prefix} {cy_suffix}"
        if py_col in cols:
            period_map[f"{prefix.replace('/', '')}_PY"] = py_col
        if cy_col in cols:
            period_map[f"{prefix.replace('/', '')}_CY"] = cy_col

    return period_map


# =============================================================================
# LONG FORMAT PERIOD DETECTION
# =============================================================================

def _parse_month_year(col_str):
    """
    Parses a column name like "Apr 2026" into (month_num, year_int).
    Returns None if the column name does not match the pattern.
    """
    match = re.match(r'^([A-Z][a-z]{2})\s+(\d{4})$', str(col_str))
    if match:
        month_str, year_str = match.group(1), match.group(2)
        if month_str in MONTH_MAP:
            return MONTH_MAP[month_str], int(year_str)
    return None


def detect_all_monthly_cols(df):
    """
    Finds all monthly columns in the DataFrame.
    Monthly columns match the pattern "Mon YYYY" (e.g. "Apr 2026").
    Returns list of column names sorted chronologically.
    """
    monthly = []
    for col in df.columns:
        parsed = _parse_month_year(col)
        if parsed:
            monthly.append((parsed[1], parsed[0], col))  # (year, month, col_name)

    # Sort chronologically
    monthly.sort()
    return [item[2] for item in monthly]


def detect_latest_month(monthly_cols):
    """
    Identifies the most recent month from a list of monthly columns.
    Returns (latest_col, prior_year_col) e.g. ("Apr 2026", "Apr 2025").
    """
    if not monthly_cols:
        return None, None

    latest_col = monthly_cols[-1]
    parsed     = _parse_month_year(latest_col)
    if not parsed:
        return None, None

    month_num, year = parsed
    prior_col = f"{MONTH_ABBR[month_num]} {year - 1}"
    return latest_col, prior_col


def detect_long_prebuilt_periods(df, latest_month, prior_month):
    """
    Detects pre-built period columns (L3M, YTD, MAT) in long-format files.
    Looks for columns matching "L3M {month} {year}", "YTD ...", "MAT ..."
    Assigns CY (current year) and PY (prior year) versions.

    Returns dict of period_key -> column name.
    """
    cols       = df.columns.tolist()
    period_map = {}

    # Extract month and year from latest and prior month strings
    parsed_cy = _parse_month_year(latest_month)
    parsed_py = _parse_month_year(prior_month)

    if not parsed_cy or not parsed_py:
        print(f"  WARNING: Could not parse latest/prior month for period detection")
        return {}

    cy_month_str = MONTH_ABBR[parsed_cy[0]]
    cy_year      = parsed_cy[1]
    py_month_str = MONTH_ABBR[parsed_py[0]]
    py_year      = parsed_py[1]

    # Mth = the monthly column itself
    if latest_month in cols:
        period_map["Mth_CY"] = latest_month
    if prior_month in cols:
        period_map["Mth_PY"] = prior_month

    # L3M, YTD, MAT — look for pattern "PREFIX Mon YYYY"
    for prefix in ["L3M", "YTD", "MAT"]:
        cy_col = f"{prefix} {cy_month_str} {cy_year}"
        py_col = f"{prefix} {py_month_str} {py_year}"
        if cy_col in cols:
            period_map[f"{prefix}_CY"] = cy_col
        else:
            print(f"  WARNING: Expected column '{cy_col}' not found")
        if py_col in cols:
            period_map[f"{prefix}_PY"] = py_col
        else:
            print(f"  WARNING: Expected column '{py_col}' not found")

    return period_map


def detect_l6m_months(monthly_cols, latest_month):
    """
    Identifies the 6 monthly columns for L6M derivation.
    CY: the 6 most recent months ending at latest_month.
    PY: the same 6 months one year prior.

    Returns (l6m_cy_cols, l6m_py_cols).
    """
    if latest_month not in monthly_cols:
        print(f"  WARNING: Latest month '{latest_month}' not in monthly columns")
        return [], []

    idx = monthly_cols.index(latest_month)
    if idx < 5:
        print(f"  WARNING: Not enough months before '{latest_month}' for L6M")
        return [], []

    l6m_cy = monthly_cols[idx - 5: idx + 1]  # 6 months ending at latest

    # Build PY equivalents by shifting year back by 1
    l6m_py = []
    for col in l6m_cy:
        parsed = _parse_month_year(col)
        if parsed:
            py_col = f"{MONTH_ABBR[parsed[0]]} {parsed[1] - 1}"
            l6m_py.append(py_col)

    # Validate PY months exist in the file
    missing_py = [m for m in l6m_py if m not in monthly_cols]
    if missing_py:
        print(f"  WARNING: These PY L6M months not found in file: {missing_py}")

    return l6m_cy, l6m_py


# =============================================================================
# MAIN DETECTION FUNCTION
# =============================================================================

def detect_all(df):
    """
    Master detection function. Analyses the DataFrame and returns
    a fully populated DetectedConfig object with all period
    mappings auto-detected from the file.

    Args:
        df : loaded DataFrame (before any filtering)

    Returns:
        DetectedConfig object
    """
    print("\n  Running auto-detection...")
    cfg = DetectedConfig()

    # Detect format
    cfg.fmt = detect_format(df)

    if cfg.fmt == "wide":
        # Wide format: simple year-suffix labels
        cfg.periods = detect_wide_periods(df)
        # L6M already pre-built in wide format — no derivation needed
        cfg.l6m_months_cy = []
        cfg.l6m_months_py = []

    else:
        # Long format: dated column labels
        cfg.all_monthly   = detect_all_monthly_cols(df)
        print(f"  Monthly columns found: {len(cfg.all_monthly)} "
              f"({cfg.all_monthly[0] if cfg.all_monthly else 'none'} "
              f"to {cfg.all_monthly[-1] if cfg.all_monthly else 'none'})")

        cfg.latest_month, cfg.prior_month = detect_latest_month(cfg.all_monthly)
        print(f"  Latest month: {cfg.latest_month}")
        print(f"  Prior month : {cfg.prior_month}")

        cfg.periods = detect_long_prebuilt_periods(
            df, cfg.latest_month, cfg.prior_month
        )

        cfg.l6m_months_cy, cfg.l6m_months_py = detect_l6m_months(
            cfg.all_monthly, cfg.latest_month
        )
        print(f"  L6M CY months: {cfg.l6m_months_cy}")
        print(f"  L6M PY months: {cfg.l6m_months_py}")

    # Summary
    print(f"  Periods detected: {list(cfg.periods.keys())}")
    missing = [p for p in ["Mth_CY","Mth_PY","L3M_CY","L3M_PY",
                            "YTD_CY","YTD_PY","MAT_CY","MAT_PY"]
               if p not in cfg.periods]
    if missing:
        print(f"  WARNING: These periods could not be detected: {missing}")
    else:
        print(f"  All standard periods detected successfully")

    return cfg
