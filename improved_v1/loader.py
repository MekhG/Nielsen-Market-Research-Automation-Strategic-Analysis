# ============================================================
# loader.py
# ============================================================
# FORMAT: Format 1 — Single Category, Config-Driven Pipeline
#
# PURPOSE:
# This file is responsible for loading the raw source Excel
# files into pandas DataFrames. It handles three key tasks:
#
# 1. FORMAT AUTO-DETECTION:
#    Automatically detects whether the source file is in wide
#    format (one row per brand x geography x metric, with
#    metrics as separate columns — e.g. Lozenge-style) or
#    long format (one row per brand x geography, with metrics
#    stacked in a single Metric column — e.g. Sanitizer-style).
#    Detection is done by checking if a "Metric" column exists.
#    No manual format specification is needed in config.py.
#
# 2. STRUCTURAL VALIDATION:
#    Before reading any data, validates that all expected
#    columns exist in the loaded file. If any column is missing
#    or renamed, the pipeline stops immediately with a clear
#    error message identifying exactly which columns are missing
#    and in which file. This prevents silent wrong output.
#    Also validates that both files have identical column
#    structures when a second file is provided.
#
# 3. TWO-FILE MERGE (for long format categories):
#    When a category comes as two files (e.g. main + remaining
#    geographies), merges them with an explicit overlap rule —
#    the first file takes priority for any geography appearing
#    in both. The overlap is logged during every run so nothing
#    is silent.
#
# 4. FUZZY GEOGRAPHY MATCHING:
#    Applies fuzzy matching to geography names to catch minor
#    spelling or capitalisation differences between monthly
#    files. A threshold of 90/100 is used — matches below this
#    score are flagged as warnings rather than silently skipped.
#
# THIS FILE DOES NOT NEED TO BE EDITED BETWEEN RUNS.
# All file paths, sheet names and column names are read from
# config.py.
# ============================================================

import sys
import pandas as pd
from thefuzz import process, fuzz
from config import (
    SOURCE_FILE, SOURCE_SHEET, SOURCE_HEADER_ROW,
    HAS_SECOND_FILE, SOURCE_FILE_2, SOURCE_SHEET_2,
    WIDE_COLS, LONG_COLS, METRIC_NAMES,
    WIDE_PERIODS, LONG_PERIODS,
    L6M_MONTHS_CY, L6M_MONTHS_PY,
    WIDE_GEO_MAP, LONG_GEO_MAP,
)

FUZZY_THRESHOLD = 90


# =============================================================================
# FORMAT AUTO-DETECTION
# =============================================================================

def detect_format(df):
    """
    Detects whether a DataFrame is in wide or long format.
    Wide format: metrics are separate columns (e.g. Lozenge-style)
    Long format: metrics are stacked in a single Metric column (e.g. Sanitizer-style)
    Detection is based on presence of the Metric column from LONG_COLS config.
    """
    metric_col = LONG_COLS["metric"]
    if metric_col in df.columns:
        print(f"  Format detected: LONG (metric column '{metric_col}' found)")
        return "long"
    else:
        print(f"  Format detected: WIDE (no '{metric_col}' column)")
        return "wide"


# =============================================================================
# VALIDATION
# =============================================================================

def validate_columns(df, expected_cols, filename):
    """
    Checks that all expected columns exist in the loaded file.
    Raises a clear, descriptive error if any are missing.
    Also checks that the file has a reasonable number of rows.
    """
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"\n{'='*55}"
            f"\nFILE STRUCTURE ERROR in: {filename}"
            f"\nThe following expected columns are missing:"
            f"\n  {missing}"
            f"\nPlease check if column names have changed"
            f"\nand update config.py accordingly."
            f"\n{'='*55}"
        )
    if len(df) < 5:
        raise ValueError(
            f"\n{'='*55}"
            f"\nFILE LOAD ERROR in: {filename}"
            f"\nOnly {len(df)} rows loaded — file may not have"
            f"\nloaded correctly. Check SOURCE_HEADER_ROW in config.py."
            f"\n{'='*55}"
        )
    print(f"  Structure validated — all expected columns present")


def validate_wide(df, filename):
    """Validates a wide-format file has all expected columns."""
    expected = list(WIDE_COLS.values()) + list(WIDE_PERIODS.values())
    validate_columns(df, expected, filename)


def validate_long(df, filename):
    """Validates a long-format file has all expected columns."""
    expected = (
        list(LONG_COLS.values()) +
        list(LONG_PERIODS.values()) +
        L6M_MONTHS_CY +
        L6M_MONTHS_PY
    )
    validate_columns(df, expected, filename)


# =============================================================================
# FUZZY GEOGRAPHY MATCHING
# =============================================================================

def fuzzy_match_wide_geo(value, geo_map):
    """
    Matches a wide-format Market string to known geography keys.
    Tries exact match first, falls back to fuzzy match.
    Returns matched key or None if no match found above threshold.
    """
    if value in geo_map:
        return value
    known = list(geo_map.keys())
    match, score = process.extractOne(value, known, scorer=fuzz.ratio)
    if score >= FUZZY_THRESHOLD:
        print(f"  FUZZY MATCH (geo): '{value}' -> '{match}' (score {score})")
        return match
    print(f"  WARNING: No geo match for '{value}' (best: '{match}', score {score})")
    return None


def fuzzy_match_long_geo(market, zone, state, geo_map):
    """
    Matches a long-format (Market, Zone, State) tuple to known geography keys.
    Tries exact match first, falls back to component-wise fuzzy match.
    Returns matched tuple or None if no match found above threshold.
    """
    geo_key = (market, zone, state)
    if geo_key in geo_map:
        return geo_key
    known_keys = list(geo_map.keys())
    best_score, best_key = 0, None
    for k in known_keys:
        score = (fuzz.ratio(market, k[0]) + fuzz.ratio(zone, k[1]) + fuzz.ratio(state, k[2])) / 3
        if score > best_score:
            best_score, best_key = score, k
    if best_score >= FUZZY_THRESHOLD:
        print(f"  FUZZY MATCH (geo): {geo_key} -> {best_key} (score {best_score:.0f})")
        return best_key
    print(f"  WARNING: No geo match for {geo_key} (best: {best_key}, score {best_score:.0f})")
    return None


def apply_fuzzy_geo_wide(df):
    """Adds matched_geo column to wide-format DataFrame using fuzzy matching."""
    print("  Applying geography matching (wide)...")
    df["matched_geo"] = [fuzzy_match_wide_geo(v, WIDE_GEO_MAP)
                         for v in df[WIDE_COLS["geography"]]]
    return df


def apply_fuzzy_geo_long(df):
    """Adds matched_geo_key column to long-format DataFrame using fuzzy matching."""
    print("  Applying geography matching (long)...")
    df["matched_geo_key"] = [
        fuzzy_match_long_geo(
            row[LONG_COLS["market"]],
            row[LONG_COLS["zone"]],
            row[LONG_COLS["state"]],
            LONG_GEO_MAP
        )
        for _, row in df.iterrows()
    ]
    return df


# =============================================================================
# CORE LOADERS
# =============================================================================

def _load_single_file(filepath, sheet, header_row, filename_label):
    """
    Loads a single Excel file into a DataFrame.
    Strips whitespace from string columns.
    Auto-detects format and validates structure.
    For long format, adds geo_key column for overlap detection.
    Returns (DataFrame, format_string).
    """
    print(f"\nLoading: {filename_label}")
    df = pd.read_excel(filepath, sheet_name=sheet, header=header_row)

    # Strip whitespace from string columns
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())

    # Detect format
    fmt = detect_format(df)

    # Validate structure
    if fmt == "wide":
        validate_wide(df, filename_label)
        df = apply_fuzzy_geo_wide(df)
    else:
        validate_long(df, filename_label)
        df["geo_key"] = list(zip(
            df[LONG_COLS["market"]],
            df[LONG_COLS["zone"]],
            df[LONG_COLS["state"]]
        ))
        df = apply_fuzzy_geo_long(df)

    print(f"  Loaded: {len(df)} rows, {len(df.columns)} columns")
    return df, fmt


def load_source():
    """
    Main loader function. Loads the source file(s) and returns
    a clean DataFrame ready for transformation.

    If HAS_SECOND_FILE is True, loads both files and merges them
    with the overlap rule: first file takes priority for any
    geography present in both.

    Returns (DataFrame, format_string).
    """
    df1, fmt = _load_single_file(
        SOURCE_FILE, SOURCE_SHEET, SOURCE_HEADER_ROW,
        SOURCE_FILE.split("/")[-1]
    )

    if not HAS_SECOND_FILE:
        return df1, fmt

    # Load second file
    df2, fmt2 = _load_single_file(
        SOURCE_FILE_2, SOURCE_SHEET_2, SOURCE_HEADER_ROW,
        SOURCE_FILE_2.split("/")[-1]
    )

    # Validate both files have same format
    if fmt != fmt2:
        raise ValueError(
            f"\n{'='*55}"
            f"\nFORMAT MISMATCH between source files:"
            f"\n  File 1 format: {fmt}"
            f"\n  File 2 format: {fmt2}"
            f"\nBoth files must be the same format."
            f"\n{'='*55}"
        )

    # Validate both files have identical columns
    cols1 = [c for c in df1.columns if c not in ["geo_key", "matched_geo", "matched_geo_key"]]
    cols2 = [c for c in df2.columns if c not in ["geo_key", "matched_geo", "matched_geo_key"]]
    if cols1 != cols2:
        raise ValueError(
            f"\n{'='*55}"
            f"\nCOLUMN MISMATCH between source files."
            f"\nFile 1 columns: {cols1}"
            f"\nFile 2 columns: {cols2}"
            f"\n{'='*55}"
        )

    # Merge with overlap rule (long format only — uses geo_key)
    if fmt == "long":
        geo_in_file1 = set(df1["geo_key"].unique())
        overlapping  = df2[df2["geo_key"].isin(geo_in_file1)]["geo_key"].unique()
        print(f"\n  Overlapping geo_keys dropped from File 2: {list(overlapping)}")
        df2_clean = df2[~df2["geo_key"].isin(geo_in_file1)]
        df_combined = pd.concat([df1, df2_clean], ignore_index=True)
    else:
        # Wide format — merge on matched_geo
        geo_in_file1 = set(df1["matched_geo"].unique())
        overlapping  = df2[df2["matched_geo"].isin(geo_in_file1)]["matched_geo"].unique()
        print(f"\n  Overlapping geographies dropped from File 2: {list(overlapping)}")
        df2_clean = df2[~df2["matched_geo"].isin(geo_in_file1)]
        df_combined = pd.concat([df1, df2_clean], ignore_index=True)

    print(f"\n  Combined: {len(df_combined)} rows")
    return df_combined, fmt
