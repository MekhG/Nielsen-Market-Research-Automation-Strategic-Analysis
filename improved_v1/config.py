import os

# FILE PATHS
INPUT_DIR    = "input"
OUTPUT_DIR   = "output"
CATEGORY_NAME = "Lozenge"
SOURCE_FILE  = f"{INPUT_DIR}/Lozenge Hotsheet.xlsx"
TEMPLATE_FILE = f"{INPUT_DIR}/Output_Template.xlsx"
OUTPUT_FILE  = f"{OUTPUT_DIR}/Output_{CATEGORY_NAME}.xlsx"
HAS_SECOND_FILE = False
SOURCE_FILE_2   = ""
SOURCE_SHEET    = "Cat x Brand x Seg"
SOURCE_HEADER_ROW = 0
SOURCE_SHEET_2  = "Brands"

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

METRIC_NAMES = {
    "Sales Value" : "Sales Value in Cr.",
    "Sales Units" : "Sales Unit in Mn",
    "MS Val"      : "MS% Val",
    "Store Count" : "Dealers 000 (Latest)",
    "WD"          : "WTD Dist%",
}

WIDE_ROLES = {
    "focal"      : {"brand": "ZESTOL",       "level": "Brand",    "segment": "ZESTOL"},
    "category"   : {"brand": "THROAT DROPS", "level": "Category", "segment": "THROAT DROPS"},
    "competitor" : {"brand": "MINTEX",        "level": "Brand",    "segment": "MINTEX"},
}

LONG_ROLES = {
    "focal"      : {"brand_family": "CLEARO",     "product_name": "Total"},
    "category"   : {"brand_family": "Total",      "product_name": "Total"},
    "competitor" : {"brand_family": "PURESHIELD", "product_name": "Total"},
}

WIDE_PERIODS = {
    "Mth_PY": "Mth 25", "Mth_CY": "Mth 26",
    "L3M_PY": "L3M 25", "L3M_CY": "L3M 26",
    "L6M_PY": "L6M 25", "L6M_CY": "L6M 26",
    "YTD_PY": "YTD 25", "YTD_CY": "YTD 26",
    "MAT_PY": "MAT 25", "MAT_CY": "MAT 26",
}

LONG_PERIODS = {
    "Mth_PY": "Apr 2025", "Mth_CY": "Apr 2026",
    "L3M_PY": "L3M Apr 2025", "L3M_CY": "L3M Apr 2026",
    "YTD_PY": "YTD Apr 2025", "YTD_CY": "YTD Apr 2026",
    "MAT_PY": "MAT Apr 2025", "MAT_CY": "MAT Apr 2026",
}

L6M_MONTHS_CY = ["Nov 2025","Dec 2025","Jan 2026","Feb 2026","Mar 2026","Apr 2026"]
L6M_MONTHS_PY = ["Nov 2024","Dec 2024","Jan 2025","Feb 2025","Mar 2025","Apr 2025"]
L6M_SUM_METRICS = ["Sales Value in Cr.", "Sales Unit in Mn"]
L6M_AVG_METRICS = ["MS% Val", "Dealers 000 (Latest)", "WTD Dist%"]

WIDE_GEO_MAP = {
    "INDIA (U+R)"            : "All India (Total)",
    "INDIA (U+R) NORTH ZONE" : "North Zone",
    "INDIA (U+R) DELHI"      : "Delhi",
    "INDIA (U+R) PUNJAB"     : "Punjab",
    "INDIA (U+R) SOUTH ZONE" : "South Zone",
    "INDIA (U+R) KARNATAKA"  : "Karnataka",
    "INDIA (U+R) TAMIL NADU" : "Tamil Nadu",
}

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
TEMPLATE_SHEET = "Zestol"

TEMPLATE_GEO_ROWS = {
    "All India (Total)": 7,  "North Zone": 8,
    "Delhi": 9,              "Punjab": 10,
    "South Zone": 11,        "Karnataka": 12,
    "Tamil Nadu": 13,        "East Zone": 14,
    "West Bengal": 15,       "West Zone": 16,
    "Gujarat": 17,           "Maharashtra": 18,
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
    "Mth_PY": 0, "Mth_CY": 1,
    "L3M_PY": 2, "L3M_CY": 3,
    "L6M_PY": 4, "L6M_CY": 5,
    "YTD_PY": 6, "YTD_CY": 7,
    "MAT_PY": 8, "MAT_CY": 9,
}

TEMPLATE_COL_MAP = {}
for (role, metric), start_col in BLOCK_STARTS.items():
    for period_key, offset in PERIOD_OFFSETS.items():
        TEMPLATE_COL_MAP[(role, metric, period_key)] = start_col + offset
