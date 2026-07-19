## Configuration (config.py):Centralises all parameters the analyst may need to update each month — file paths,
##sheet names, column mappings, metric names, period definitions, brand roles and geography mappings for both
## Lozenge and Sanitizer data. This is the only file that needs to be edited between monthly runs.

%%writefile /content/nielsen/config.py
# =============================================================================
# config.py
# The ONLY file that needs to be updated each month.
# =============================================================================

# -----------------------------------------------------------------------------
# FILE PATHS
# -----------------------------------------------------------------------------
INPUT_DIR  = "/content/nielsen/input"
OUTPUT_DIR = "/content/nielsen/output"

LOZENGE_FILE             = f"{INPUT_DIR}/Lozenge Hotsheet.xlsx"
SANITIZER_MAIN_FILE      = f"{INPUT_DIR}/Sanitizer Hotsheet.xlsx"
SANITIZER_REMAINING_FILE = f"{INPUT_DIR}/Sanitizer Hotsheet - Remaining.xlsx"
TEMPLATE_FILE            = f"{INPUT_DIR}/Output_Template.xlsx"
OUTPUT_FILE              = f"{OUTPUT_DIR}/Output_Filled.xlsx"

# -----------------------------------------------------------------------------
# LOZENGE FILE SETTINGS
# Update column names below if they change in next month's file.
# -----------------------------------------------------------------------------
LOZENGE_SHEET      = "Cat x Brand x Seg"
LOZENGE_HEADER_ROW = 0   # zero-indexed (row 1 in Excel)

LOZENGE_COLS = {
    "brand"    : "Product",
    "segment"  : "Segment",
    "level"    : "Level",
    "geography": "Market",
    "measure"  : "Measures",
}

# Metric names as they appear in the Measures column
LOZENGE_METRIC_NAMES = {
    "Sales Value" : "Sales Value in Cr.",
    "Sales Units" : "Sales Unit in Mn",
    "MS Val"      : "MS% Val",
    "Store Count" : "Dealers 000 (Latest)",
    "WD"          : "WTD Dist%",
}

# *** UPDATE THESE EVERY MONTH ***
# Column names for each period in the Lozenge file
LOZENGE_PERIODS = {
    "Mth_PY"  : "Mth 25",
    "Mth_CY"  : "Mth 26",
    "L3M_PY"  : "L3M 25",
    "L3M_CY"  : "L3M 26",
    "L6M_PY"  : "L6M 25",
    "L6M_CY"  : "L6M 26",
    "YTD_PY"  : "YTD 25",
    "YTD_CY"  : "YTD 26",
    "MAT_PY"  : "MAT 25",
    "MAT_CY"  : "MAT 26",
}

# Brand/role definitions for the Lozenge file
# Rule: brand total row = Level=="Brand" AND Segment==Product (same value)
LOZENGE_ROLES = {
    "focal"      : {"brand": "ZESTOL",      "level": "Brand",    "segment": "ZESTOL"},
    "category"   : {"brand": "THROAT DROPS","level": "Category", "segment": "THROAT DROPS"},
    "competitor" : {"brand": "MINTEX",       "level": "Brand",    "segment": "MINTEX"},
}


# Geography mapping: source value → template row label
LOZENGE_GEO_MAP = {
    "INDIA (U+R)"            : "All India (Total)",
    "INDIA (U+R) NORTH ZONE" : "North Zone",
    "INDIA (U+R) DELHI"      : "Delhi",
    "INDIA (U+R) PUNJAB"     : "Punjab",
    "INDIA (U+R) SOUTH ZONE" : "South Zone",
    "INDIA (U+R) KARNATAKA"  : "Karnataka",
    "INDIA (U+R) TAMIL NADU" : "Tamil Nadu",
    # East Zone, West Bengal, West Zone, Gujarat, Maharashtra
    # are NOT present in the Lozenge file — these will be left blank
}

# -----------------------------------------------------------------------------
# SANITIZER FILE SETTINGS
# Update column names below if they change in next month's file.
# -----------------------------------------------------------------------------
SANITIZER_SHEET      = "Brands"
SANITIZER_HEADER_ROW = 0   # zero-indexed (row 1 in Excel)

SANITIZER_COLS = {
    "market"      : "Market",
    "zone"        : "Zone",
    "state"       : "State",
    "brand_family": "Brand Family",
    "product_name": "Product Name",
    "metric"      : "Metric",
}

# Metric names as they appear in the Metric column
SANITIZER_METRIC_NAMES = {
    "Sales Value" : "Sales Value in Cr.",
    "Sales Units" : "Sales Unit in Mn",
    "MS Val"      : "MS% Val",
    "Store Count" : "Dealers 000 (Latest)",
    "WD"          : "WTD Dist%",
}

SANITIZER_ROLES = {
    "focal"      : {"brand_family": "CLEARO",     "product_name": "Total"},
    "category"   : {"brand_family": "Total",      "product_name": "Total"},
    "competitor" : {"brand_family": "PURESHIELD", "product_name": "Total"},
}

# *** UPDATE THESE EVERY MONTH ***
# Pre-built period column names in the Sanitizer file
SANITIZER_PERIODS = {
    "Mth_PY"  : "Apr 2025",
    "Mth_CY"  : "Apr 2026",
    "L3M_PY"  : "L3M Apr 2025",
    "L3M_CY"  : "L3M Apr 2026",
    "YTD_PY"  : "YTD Apr 2025",
    "YTD_CY"  : "YTD Apr 2026",
    "MAT_PY"  : "MAT Apr 2025",
    "MAT_CY"  : "MAT Apr 2026",
    # L6M is derived — see L6M_MONTHS below
}

# *** UPDATE THESE EVERY MONTH ***
# The 6 monthly columns used to derive L6M (shift forward by 1 each month)
L6M_MONTHS_CY = ["Nov 2025", "Dec 2025", "Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026"]
L6M_MONTHS_PY = ["Nov 2024", "Dec 2024", "Jan 2025", "Feb 2025", "Mar 2025", "Apr 2025"]

# Metrics that are SUMMED for L6M (additive)
L6M_SUM_METRICS = ["Sales Value in Cr.", "Sales Unit in Mn"]
# Metrics that are AVERAGED for L6M (non-additive: ratios and counts)
L6M_AVG_METRICS = ["MS% Val", "Dealers 000 (Latest)", "WTD Dist%"]

# Geography mapping: (Market, Zone, State) tuple → template row label
SANITIZER_GEO_MAP = {
    ("ALL INDIA", "Total", "Total")     : "All India (Total)",
    ("Zone",      "North", "Total")     : "North Zone",
    ("Zone",      "South", "Total")     : "South Zone",
    ("Zone",      "East",  "Total")     : "East Zone",
    ("Zone",      "West",  "Total")     : "West Zone",
    ("State",     "North", "Delhi")     : "Delhi",
    ("State",     "North", "Punjab")    : "Punjab",
    ("State",     "South", "Karnataka") : "Karnataka",
    ("State",     "South", "Tamil Nadu"): "Tamil Nadu",
    ("State",     "East",  "West Bengal"): "West Bengal",
    ("State",     "West",  "Gujarat")   : "Gujarat",
    ("State",     "West",  "Maharashtra"): "Maharashtra",
}

# Overlap rule: ALL INDIA appears in both sanitizer files.
# Main file takes priority — matching rows in Remaining file are dropped.
SANITIZER_OVERLAP_RULE = "main_file_priority"

# -----------------------------------------------------------------------------
# OUTPUT TEMPLATE STRUCTURE
# Do NOT change these unless the template itself changes.
# -----------------------------------------------------------------------------
TEMPLATE_SHEET = "Zestol"
TEMPLATE_SHEET = "Clearo"

# Row numbers in the template (1-indexed, as Excel counts them)
TEMPLATE_DATA_START_ROW = 7   # Row 7 = All India (Total)

# Geography row mapping: label → Excel row number
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

# Column mapping: (role, metric, period_key) → Excel column number
# Columns are 1-indexed (A=1, B=2, C=3 ...)
# Each block is 10 columns wide (5 periods x 2 years)
# Within each block: Mth25, Mth26, L3M25, L3M26, L6M25, L6M26, YTD25, YTD26, MAT25, MAT26

TEMPLATE_COL_MAP = {}

# Block start columns (1-indexed: B=2)
BLOCK_STARTS = {
    ("focal",      "Sales Value")  :  2,   # B
    ("focal",      "Sales Units")  : 12,   # L
    ("focal",      "MS Val")       : 22,   # V
    ("focal",      "Store Count")  : 32,   # AF
    ("focal",      "WD")           : 42,   # AP
    ("category",   "Sales Value")  : 52,   # AZ
    ("category",   "Sales Units")  : 62,   # BJ
    ("category",   "Store Count")  : 72,   # BT
    ("competitor", "Sales Value")  : 82,   # CD
    ("competitor", "Sales Units")  : 92,   # CN
    ("competitor", "MS Val")       : 102,  # CX
    ("competitor", "Store Count")  : 112,  # DH
    ("competitor", "WD")           : 122,  # DR
}

# Period offset within each block
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

# Build the full column map
for (role, metric), start_col in BLOCK_STARTS.items():
    for period_key, offset in PERIOD_OFFSETS.items():
        TEMPLATE_COL_MAP[(role, metric, period_key)] = start_col + offset
