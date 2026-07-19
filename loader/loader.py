## Data Loading (loader.py)
## First, structural validation is added before any data
##is read — if expected columns are missing the pipeline stops immediately with a clear error
##message identifying exactly which columns are missing and in which file. Second, both Sanitizer
##files are validated to have identical column structures before merging, preventing silent NaN values in the combined dataset.

%%writefile /content/nielsen/loader.py
import sys
sys.path.append("/content/nielsen")

import pandas as pd
from thefuzz import process, fuzz
from config import (
    LOZENGE_FILE, LOZENGE_SHEET, LOZENGE_HEADER_ROW,
    SANITIZER_MAIN_FILE, SANITIZER_REMAINING_FILE,
    SANITIZER_SHEET, SANITIZER_HEADER_ROW,
    SANITIZER_COLS, SANITIZER_GEO_MAP,
    LOZENGE_COLS, LOZENGE_METRIC_NAMES, LOZENGE_PERIODS,
    LOZENGE_GEO_MAP, SANITIZER_METRIC_NAMES, SANITIZER_PERIODS,
    L6M_MONTHS_CY, L6M_MONTHS_PY
)


# =============================================================================
# FUZZY MATCHING
# =============================================================================

FUZZY_THRESHOLD = 90  # minimum score to consider a match (0-100)


def fuzzy_match_lozenge_geo(value, geo_map):
    """
    Tries to match a Lozenge Market string to our known geography map.
    First tries exact match, then fuzzy match if exact fails.

    Returns:
        matched key from geo_map, or None if no match found
    """
    # Step 1 — try exact match first
    if value in geo_map:
        return value

    # Step 2 — try fuzzy match against known keys
    known_geos = list(geo_map.keys())
    match, score = process.extractOne(
        value, known_geos, scorer=fuzz.ratio
    )

    if score >= FUZZY_THRESHOLD:
        print(f"  FUZZY MATCH (Lozenge geo): '{value}' → '{match}' (score {score})")
        return match

    print(f"  WARNING: No geo match found for '{value}' (best match '{match}' score {score})")
    return None


def fuzzy_match_sanitizer_geo(market, zone, state, geo_map):
    """
    Tries to match a Sanitizer (Market, Zone, State) tuple to our known geo map.
    First tries exact match, then fuzzy match on each component if exact fails.

    Returns:
        matched tuple key from geo_map, or None if no match found
    """
    geo_key = (market, zone, state)

    # Step 1 — try exact match first
    if geo_key in geo_map:
        return geo_key

    # Step 2 — try fuzzy match on each component separately
    known_keys = list(geo_map.keys())

    best_score = 0
    best_key   = None

    for known_key in known_keys:
        # Score each component separately then average
        score_market = fuzz.ratio(market, known_key[0])
        score_zone   = fuzz.ratio(zone,   known_key[1])
        score_state  = fuzz.ratio(state,  known_key[2])
        avg_score    = (score_market + score_zone + score_state) / 3

        if avg_score > best_score:
            best_score = avg_score
            best_key   = known_key

    if best_score >= FUZZY_THRESHOLD:
        print(f"  FUZZY MATCH (Sanitizer geo): {geo_key} → {best_key} (score {best_score:.0f})")
        return best_key

    print(f"  WARNING: No geo match found for {geo_key} "
          f"(best match {best_key} score {best_score:.0f})")
    return None


def apply_fuzzy_geo_lozenge(df):
    """
    Adds a matched_geo column to Lozenge DataFrame.
    Uses fuzzy matching to map Market values to known geography keys.
    """
    print("  Applying fuzzy geography matching for Lozenge...")

    matched = []
    for val in df[LOZENGE_COLS["geography"]]:
        matched.append(fuzzy_match_lozenge_geo(val, LOZENGE_GEO_MAP))

    df["matched_geo"] = matched
    return df


def apply_fuzzy_geo_sanitizer(df):
    """
    Adds a matched_geo_key column to Sanitizer DataFrame.
    Uses fuzzy matching to map (Market, Zone, State) tuples
    to known geography keys.
    """
    print("  Applying fuzzy geography matching for Sanitizer...")

    matched = []
    for _, row in df.iterrows():
        matched.append(fuzzy_match_sanitizer_geo(
            row[SANITIZER_COLS["market"]],
            row[SANITIZER_COLS["zone"]],
            row[SANITIZER_COLS["state"]],
            SANITIZER_GEO_MAP
        ))

    df["matched_geo_key"] = matched
    return df


# =============================================================================
# VALIDATION
# =============================================================================

def validate_file_structure(df, expected_cols, filename):
    """
    Checks that all expected columns exist in the loaded file.
    Fails loudly with a clear message if anything is missing.
    """
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"\n{'='*50}"
            f"\nFILE STRUCTURE ERROR in {filename}"
            f"\nThese expected columns are missing: {missing}"
            f"\nPlease check if column names have changed"
            f"\nand update config.py accordingly."
            f"\n{'='*50}"
        )

    if len(df) < 10:
        raise ValueError(
            f"\n{'='*50}"
            f"\nFILE LOAD ERROR in {filename}"
            f"\nOnly {len(df)} rows loaded — file may not have loaded correctly."
            f"\nCheck HEADER_ROW value in config.py."
            f"\n{'='*50}"
        )

    print(f"  Structure validated — all expected columns present")


def validate_lozenge(df):
    """Validates Lozenge file has all expected columns."""
    expected = [
        LOZENGE_COLS["brand"],
        LOZENGE_COLS["segment"],
        LOZENGE_COLS["level"],
        LOZENGE_COLS["geography"],
        LOZENGE_COLS["measure"],
    ]
    expected += list(LOZENGE_PERIODS.values())
    validate_file_structure(df, expected, "Lozenge_Hotsheet.xlsx")


def validate_sanitizer(df, filename):
    """Validates Sanitizer file has all expected columns."""
    expected = [
        SANITIZER_COLS["market"],
        SANITIZER_COLS["zone"],
        SANITIZER_COLS["state"],
        SANITIZER_COLS["brand_family"],
        SANITIZER_COLS["product_name"],
        SANITIZER_COLS["metric"],
    ]
    expected += list(SANITIZER_PERIODS.values())
    expected += L6M_MONTHS_CY
    expected += L6M_MONTHS_PY
    validate_file_structure(df, expected, filename)


# =============================================================================
# LOADERS
# =============================================================================

def load_lozenge():
    """
    Loads the Lozenge Hotsheet.
    Validates structure and applies fuzzy geography matching.
    """
    print("Loading Lozenge file...")

    df = pd.read_excel(
        LOZENGE_FILE,
        sheet_name=LOZENGE_SHEET,
        header=LOZENGE_HEADER_ROW
    )

    # Strip whitespace from all string columns
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())

    # Validate structure
    validate_lozenge(df)

    # Apply fuzzy geography matching
    df = apply_fuzzy_geo_lozenge(df)

    print(f"  Lozenge loaded: {len(df)} rows, {len(df.columns)} columns")
    return df


def _load_single_sanitizer(filepath):
    """
    Loads one Sanitizer file.
    Validates structure and applies fuzzy geography matching.
    """
    filename = filepath.split("/")[-1]

    df = pd.read_excel(
        filepath,
        sheet_name=SANITIZER_SHEET,
        header=SANITIZER_HEADER_ROW
    )

    # Strip whitespace from all string columns
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())

    # Validate structure
    validate_sanitizer(df, filename)

    # Add exact geo_key for overlap detection
    df["geo_key"] = list(zip(
        df[SANITIZER_COLS["market"]],
        df[SANITIZER_COLS["zone"]],
        df[SANITIZER_COLS["state"]]
    ))

    # Apply fuzzy geography matching
    df = apply_fuzzy_geo_sanitizer(df)

    return df


def load_sanitizer():
    """
    Loads and merges both Sanitizer files.
    Overlap rule: main file takes priority.
    Returns one combined clean DataFrame.
    """
    print("Loading Sanitizer main file...")
    df_main = _load_single_sanitizer(SANITIZER_MAIN_FILE)
    print(f"  Main loaded: {len(df_main)} rows")

    print("Loading Sanitizer remaining file...")
    df_remaining = _load_single_sanitizer(SANITIZER_REMAINING_FILE)
    print(f"  Remaining loaded: {len(df_remaining)} rows")

    # Validate column structures match between both files
    main_cols      = [c for c in df_main.columns
                      if c not in ["geo_key", "matched_geo_key"]]
    remaining_cols = [c for c in df_remaining.columns
                      if c not in ["geo_key", "matched_geo_key"]]

    if main_cols != remaining_cols:
        raise ValueError(
            f"\n{'='*50}"
            f"\nFILE STRUCTURE MISMATCH"
            f"\nMain and Remaining Sanitizer files have different columns."
            f"\nMain columns:      {main_cols}"
            f"\nRemaining columns: {remaining_cols}"
            f"\n{'='*50}"
        )

    # Find geo_keys that exist in the main file
    geo_keys_in_main = set(df_main["geo_key"].unique())

    # Drop those same geo_keys from the remaining file
    overlapping = df_remaining[
        df_remaining["geo_key"].isin(geo_keys_in_main)
    ]["geo_key"].unique()

    print(f"  Overlapping geo_keys dropped from Remaining: {list(overlapping)}")

    df_remaining_clean = df_remaining[
        ~df_remaining["geo_key"].isin(geo_keys_in_main)
    ]

    # Combine both files
    df_combined = pd.concat([df_main, df_remaining_clean], ignore_index=True)
    print(f"  Combined Sanitizer: {len(df_combined)} rows")

    # Warn about unknown geo_keys
    known_keys   = set(SANITIZER_GEO_MAP.keys())
    unknown_keys = set(df_combined["geo_key"].unique()) - known_keys
    if unknown_keys:
        print(f"  WARNING: These geo_keys are not in SANITIZER_GEO_MAP: {unknown_keys}")
        print(f"  These geographies will be skipped.")

    return df_combined

if __name__ == "__main__":
    # Quick test — run this file directly to verify loading works
    df_loz = load_lozenge()
    print("\nLozenge columns:", df_loz.columns.tolist())
    print(df_loz.head(3))

    print("\n" + "="*60 + "\n")

    df_san = load_sanitizer()
    print("\nSanitizer columns:", df_san.columns.tolist())
    print(df_san.head(3))
