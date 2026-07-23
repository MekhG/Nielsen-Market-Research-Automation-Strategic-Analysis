# ============================================================
# loader.py
# ============================================================
# FORMAT: Format 2 — Hands-Off Auto-Detection Pipeline
#
# PURPOSE:
# This file loads the raw source Excel files into pandas
# DataFrames and triggers auto-detection via detector.py.
# It is largely identical to Format 1 loader.py with one
# key difference:
#
# FORMAT 1 loader.py:
#   Validates columns against manually configured period
#   column names from config.py (WIDE_PERIODS, LONG_PERIODS,
#   L6M_MONTHS_CY, L6M_MONTHS_PY).
#
# FORMAT 2 loader.py:
#   Does NOT validate period column names at load time because
#   period columns are not yet known — they are discovered by
#   detector.py AFTER loading. Structural validation still
#   checks identity columns (Market, Zone, Brand Family etc.)
#   but skips period column validation.
#   After loading, calls detector.detect_all() to discover
#   all period mappings automatically.
#
# ALL OTHER BEHAVIOUR IS IDENTICAL TO FORMAT 1:
#   - Format auto-detection (wide vs long)
#   - Fuzzy geography matching
#   - Two-file merge with overlap rule
#   - Structural validation of identity columns
#   - Whitespace stripping
#
# THIS FILE DOES NOT NEED TO BE EDITED BETWEEN RUNS.
# ============================================================

import pandas as pd
from thefuzz import process, fuzz
from config import (
    SOURCE_FILE, SOURCE_SHEET, SOURCE_HEADER_ROW,
    HAS_SECOND_FILE, SOURCE_FILE_2, SOURCE_SHEET_2,
    WIDE_COLS, LONG_COLS,
    WIDE_GEO_MAP, LONG_GEO_MAP,
)
import detector

FUZZY_THRESHOLD = 90


# =============================================================================
# VALIDATION (identity columns only — no period columns)
# =============================================================================

def validate_columns(df, expected_cols, filename):
    """
    Checks that all expected identity columns exist in the file.
    Period columns are NOT validated here — they are discovered
    by detector.py after loading.
    Raises a clear error if any identity column is missing.
    """
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"\n{'='*55}"
            f"\nFILE STRUCTURE ERROR in: {filename}"
            f"\nThese expected columns are missing: {missing}"
            f"\nPlease check if column names have changed"
            f"\nand update config.py accordingly."
            f"\n{'='*55}"
        )
    if len(df) < 5:
        raise ValueError(
            f"\n{'='*55}"
            f"\nFILE LOAD ERROR in: {filename}"
            f"\nOnly {len(df)} rows loaded."
            f"\nCheck SOURCE_HEADER_ROW in config.py."
            f"\n{'='*55}"
        )
    print(f"  Identity columns validated")


def validate_wide(df, filename):
    """Validates wide-format identity columns only."""
    expected = list(WIDE_COLS.values())
    validate_columns(df, expected, filename)


def validate_long(df, filename):
    """Validates long-format identity columns only."""
    expected = list(LONG_COLS.values())
    validate_columns(df, expected, filename)


# =============================================================================
# FUZZY GEOGRAPHY MATCHING
# =============================================================================

def fuzzy_match_wide_geo(value, geo_map):
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
    geo_key = (market, zone, state)
    if geo_key in geo_map:
        return geo_key
    known_keys = list(geo_map.keys())
    best_score, best_key = 0, None
    for k in known_keys:
        score = (fuzz.ratio(market, k[0]) +
                 fuzz.ratio(zone,   k[1]) +
                 fuzz.ratio(state,  k[2])) / 3
        if score > best_score:
            best_score, best_key = score, k
    if best_score >= FUZZY_THRESHOLD:
        print(f"  FUZZY MATCH (geo): {geo_key} -> {best_key} (score {best_score:.0f})")
        return best_key
    print(f"  WARNING: No geo match for {geo_key} "
          f"(best: {best_key}, score {best_score:.0f})")
    return None


def apply_fuzzy_geo_wide(df):
    print("  Applying geography matching (wide)...")
    df["matched_geo"] = [
        fuzzy_match_wide_geo(v, WIDE_GEO_MAP)
        for v in df[WIDE_COLS["geography"]]
    ]
    return df


def apply_fuzzy_geo_long(df):
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
# CORE LOADER
# =============================================================================

def _load_single_file(filepath, sheet, header_row, filename_label):
    """
    Loads a single Excel file. Validates identity columns.
    Applies fuzzy geography matching.
    Does NOT validate period columns — handled by detector.py.
    Returns (DataFrame, format_string).
    """
    print(f"\nLoading: {filename_label}")
    df = pd.read_excel(filepath, sheet_name=sheet, header=header_row)

    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())

    fmt = detector.detect_format(df)

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
    Loads source file(s), merges if two files provided,
    then runs auto-detection to discover all period mappings.

    Returns (DataFrame, DetectedConfig).
    """
    df1, fmt = _load_single_file(
        SOURCE_FILE, SOURCE_SHEET, SOURCE_HEADER_ROW,
        SOURCE_FILE.split("/")[-1]
    )

    if not HAS_SECOND_FILE:
        detected = detector.detect_all(df1)
        return df1, detected

    df2, fmt2 = _load_single_file(
        SOURCE_FILE_2, SOURCE_SHEET_2, SOURCE_HEADER_ROW,
        SOURCE_FILE_2.split("/")[-1]
    )

    if fmt != fmt2:
        raise ValueError(
            f"\n{'='*55}"
            f"\nFORMAT MISMATCH between source files:"
            f"\n  File 1: {fmt}, File 2: {fmt2}"
            f"\n{'='*55}"
        )

    cols1 = [c for c in df1.columns
             if c not in ["geo_key","matched_geo","matched_geo_key"]]
    cols2 = [c for c in df2.columns
             if c not in ["geo_key","matched_geo","matched_geo_key"]]
    if cols1 != cols2:
        raise ValueError(
            f"\n{'='*55}"
            f"\nCOLUMN MISMATCH between source files."
            f"\nFile 1 columns: {cols1}"
            f"\nFile 2 columns: {cols2}"
            f"\n{'='*55}"
        )

    if fmt == "long":
        geo_in_file1 = set(df1["geo_key"].unique())
        overlapping  = df2[df2["geo_key"].isin(geo_in_file1)]["geo_key"].unique()
        print(f"\n  Overlapping geo_keys dropped from File 2: {list(overlapping)}")
        df2_clean    = df2[~df2["geo_key"].isin(geo_in_file1)]
    else:
        geo_in_file1 = set(df1["matched_geo"].unique())
        overlapping  = df2[df2["matched_geo"].isin(geo_in_file1)]["matched_geo"].unique()
        print(f"\n  Overlapping geos dropped from File 2: {list(overlapping)}")
        df2_clean    = df2[~df2["matched_geo"].isin(geo_in_file1)]

    df_combined = pd.concat([df1, df2_clean], ignore_index=True)
    print(f"\n  Combined: {len(df_combined)} rows")

    detected = detector.detect_all(df_combined)
    return df_combined, detected
