# ============================================================
# config.py
# ============================================================
# FORMAT: Format 2 — Hands-Off Auto-Detection Pipeline
#
# PURPOSE:
# This is the central configuration file for the Format 2
# Nielsen Automation Pipeline. Compared to Format 1, this
# file requires significantly fewer manual updates between
# monthly runs because the pipeline auto-detects:
#   - File format (wide vs long)
#   - Latest month from column names
#   - All period columns (Mth, L3M, L6M, YTD, MAT)
#   - L6M monthly columns (6 most recent months)
#
# WHAT STILL NEEDS MANUAL UPDATE:
#   - File paths (when new files arrive)
#   - Brand role names (when category changes)
#   - Geography mappings (when geographies change)
#   - Template sheet name (when category changes)
#
# WHAT NEVER NEEDS MANUAL UPDATE:
#   - Period column names (auto-detected from file)
#   - L6M month list (auto-detected from file)
#   - File format (auto-detected from file)
#
# HOW TO USE FOR A NEW CATEGORY:
#   1. Drop new files into the input/ folder
#   2. Update SOURCE_FILE, CATEGORY_NAME, TEMPLATE_SHEET
#   3. Update brand role names
#   4. Update geography mappings if geographies differ
#   5. Run: python main.py
#   No period column names need to be touched.
#
# HOW TO USE FOR A NEW MONTH (SAME CATEGORY):
#   1. Drop new files into the input/ folder
#   2. Run: python main.py
#   Nothing else needs to change.
# ============================================================

import os

# -----------------------------------------------------------------------------
# FILE PATHS
# -----------------------------------------------------------------------------
INPUT_DIR     = "input"
OUTPUT_DIR    = "output"

CATEGORY_NAME  = "Lozenge"
SOURCE_FILE    = f"{INPUT_DIR}/Lozenge Hotsheet.xlsx"
TEMPLATE_FILE  = f"{INPUT_DIR}/Output_Template.xlsx"
OUTPUT_FILE    = f"{OUTPUT_DIR}/Output_{CATEGORY_NAME}.xlsx"

# For categories that come as two files (e.g. Sanitizer main + remaining)
# Set HAS_SECOND_FILE = True and provide the second file path
HAS_SECOND_FILE = False
SOURCE_FILE_2   = f"{INPUT_DIR}/Sanitizer Hotsheet - Remaining.xlsx"

# -----------------------------------------------------------------------------
# SOURCE FILE SETTINGS
# -----------------------------------------------------------------------------
SOURCE_SHEET      = "Cat x Brand x Seg"
SOURCE_HEADER_ROW = 0
SOURCE_SHEET_2    = "Brands"

# -----------------------------------------------------------------------------
# COLUMN MAPPINGS
# Update if column names differ in the new category file
# -----------------------------------------------------------------------------
WIDE_COLS = {
    "brand"    : "Product",
    "segment"  : "Segment",
    "level"    : "Level",
    "geography": "Market",
    "measure"  : "Measures",
}

LONG_COLS = {
    "market"      : "Market",
    "zone"        : "Zone",
    "state"       : "State",
    "brand_family": "Brand Family",
    "product_name": "Product Name",
    "metric"      : "Metric",
}

# -----------------------------------------------------------------------------
# METRIC NAME MAPPINGS
# Update if source file uses different names for the same concept
# -----------------------------------------------------------------------------
METRIC_NAMES = {
    "Sales Value" : "Sales Value in Cr.",
    "Sales Units" : "Sales Unit in Mn",
    "MS Val"      : "MS% Val",
    "Store Count" : "Dealers 000 (Latest)",
    "WD"          : "WTD Dist%",
}

# -----------------------------------------------------------------------------
# BRAND ROLE DEFINITIONS
# Update brand names when switching to a new category
# -----------------------------------------------------------------------------
WIDE_ROLES = {
    "focal"      : {"brand": "STREPSILS",  "level": "Brand",    "segment": "STREPSILS"},
    "category"   : {"brand": "LOZENGES",   "level": "Category", "segment": "LOZENGES"},
    "competitor" : {"brand": "VICKS",      "level": "Brand",    "segment": "VICKS"},
}

LONG_ROLES = {
    "focal"      : {"brand_family": "DETTOL",   "product_name": "Total"},
    "category"   : {"brand_family": "Total",    "product_name": "Total"},
    "competitor" : {"brand_family": "LIFEBUOY", "product_name": "Total"},
}

# -----------------------------------------------------------------------------
# L6M AGGREGATION RULES
# Defines which metrics are summed vs averaged for L6M derivation
# Sales Value and Units accumulate over time — SUM
# MS%, Store Count, WD% are ratios/snapshots — AVERAGE
# -----------------------------------------------------------------------------
L6M_SUM_METRICS = ["Sales Value in Cr.", "Sales Unit in Mn"]
L6M_AVG_METRICS = ["MS% Val", "Dealers 000 (Latest)", "WTD Dist%"]

# -----------------------------------------------------------------------------
# GEOGRAPHY MAPPINGS
# Update when switching to a category with different geographies
#
# WIDE FORMAT: single Market text string -> template label
# -----------------------------------------------------------------------------
WIDE_GEO_MAP = {
    "INDIA (U+R)"            : "All India (Total)",
    "INDIA (U+R) NORTH ZONE" : "North Zone",
    "INDIA (U+R) DELHI"      : "Delhi",
    "INDIA (U+R) PUNJAB"     : "Punjab",
    "INDIA (U+R) SOUTH ZONE" : "South Zone",
    "INDIA (U+R) KARNATAKA"  : "Karnataka",
    "INDIA (U+R) TAMIL NADU" : "Tamil Nadu",
}

# LONG FORMAT: (Market, Zone, State) tuple -> template label
LONG_GEO_MAP = {
    ("ALL INDIA", "Total", "Total")      : "All India (Total)",
    ("Zone",      "North", "Total")      : "North Zone",
    ("Zone",      "South", "Total")      : "South Zone",
    ("Zone",      "East",  "Total")      : "East Zone",
    ("Zone",      "West",  "Total")      : "West Zone",
    ("State",     "North", "Delhi")      : "Delhi",
    ("State",     "North", "Punjab")     : "Punjab",
    ("State",     "South", "Karnataka")  : "Karnataka",
    ("State",     "South", "Tamil Nadu") : "Tamil Nadu",
    ("State",     "East",  "West Bengal"): "West Bengal",
    ("State",     "West",  "Gujarat")    : "Gujarat",
    ("State",     "West",  "Maharashtra"): "Maharashtra",
}

OVERLAP_RULE = "first_file_priority"

# -----------------------------------------------------------------------------
# OUTPUT TEMPLATE STRUCTURE
# Update TEMPLATE_SHEET when switching to a new category
# Do NOT change row/column numbers unless the template itself changes
# -----------------------------------------------------------------------------
TEMPLATE_SHEET = "Strepsils"

TEMPLATE_GEO_ROWS = {
    "All India (Total)" : 7,
    "North Zone"        : 8,
    "Delhi"             : 9,
    "Punjab"            : 10,
    "South Zone"        : 11,
    "Karnataka"         : 12,
    "Tamil Nadu"        : 13,
    "East Zone"         : 14,
    "West Bengal"       : 15,
    "West Zone"         : 16,
    "Gujarat"           : 17,
    "Maharashtra"       : 18,
}

BLOCK_STARTS = {
    ("focal",      "Sales Value")  :  2,
    ("focal",      "Sales Units")  : 12,
    ("focal",      "MS Val")       : 22,
    ("focal",      "Store Count")  : 32,
    ("focal",      "WD")           : 42,
    ("category",   "Sales Value")  : 52,
    ("category",   "Sales Units")  : 62,
    ("category",   "Store Count")  : 72,
    ("competitor", "Sales Value")  : 82,
    ("competitor", "Sales Units")  : 92,
    ("competitor", "MS Val")       : 102,
    ("competitor", "Store Count")  : 112,
    ("competitor", "WD")           : 122,
}

PERIOD_OFFSETS = {
    "Mth_PY"  : 0,
    "Mth_CY"  : 1,
    "L3M_PY"  : 2,
    "L3M_CY"  : 3,
    "L6M_PY"  : 4,
    "L6M_CY"  : 5,
    "YTD_PY"  : 6,
    "YTD_CY"  : 7,
    "MAT_PY"  : 8,
    "MAT_CY"  : 9,
}

TEMPLATE_COL_MAP = {}
for (role, metric), start_col in BLOCK_STARTS.items():
    for period_key, offset in PERIOD_OFFSETS.items():
        TEMPLATE_COL_MAP[(role, metric, period_key)] = start_col + offset
