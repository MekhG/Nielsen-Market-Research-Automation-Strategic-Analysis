# Nielsen Market Research Automation — Format 1
## Single Category, Config-Driven Pipeline

Format 1 automates the population of a Nielsen reporting template for one product category at a time. Given one or two raw Nielsen Excel files (e.g. a Lozenge Hotsheet or a Sanitizer Hotsheet), it reads the source data, extracts the correct values for three roles (focal brand, category total, competitor) across all geographies, metrics and time periods, and writes them into the correct cells of the output template.

---

## What is New in Format 1

### Compared to the Original Pipeline (v1/v2 notebooks)

| Area | Original | Format 1 |
|---|---|---|
| File format | Manually specified in config.py | Auto-detected by checking if Metric column exists |
| Two-file support | Hardcoded for Sanitizer only | Configurable for any category via HAS_SECOND_FILE |
| Output file naming | Always Output_Filled.xlsx | Named per category — Output_{CategoryName}.xlsx |
| Brand role definitions | Hardcoded for Strepsils/Dettol | Fully configurable in config.py for any brand |
| Code notes | Minimal inline comments | Detailed descriptive header on every .py file |
| Generalisation | Built for one specific assignment | Built to work for any Nielsen-style category |

### Key Improvement — Format Auto-Detection

The code automatically identifies whether the source file is in:
- **Wide format** — one row per brand × geography × metric, metrics as separate columns (e.g. Lozenge-style)
- **Long format** — metrics stacked in a single Metric column, one row per brand × geography (e.g. Sanitizer-style)

The analyst does not need to specify the format manually. Detection is done by checking whether a `Metric` column exists in the loaded file.

---

## Project Structure

```
format1/
│
├── input/                          # Drop source Excel files here
├── output/                         # Output file is generated here
│
├── config.py                       # Only file edited between runs
├── loader.py                       # File loading, validation, merge — never edit
├── transformer.py                  # Data extraction logic — never edit
├── validation.py                   # MAT cross-validation — never edit
├── writer.py                       # Template population — never edit
├── main.py                         # Pipeline orchestrator — never edit
└── requirements.txt                # Python dependencies
```

---

## Requirements

```bash
pip install -r requirements.txt
```

`requirements.txt` contains:
```
pandas
openpyxl
thefuzz
```

---

## How to Run

### Local (terminal, VS Code, Jupyter Notebook)

1. Place source Excel files in the `input/` folder
2. Update `config.py` if switching to a new category (see Configuration section)
3. Run:

```bash
python main.py
```

4. Find `Output_{CategoryName}.xlsx` in the `output/` folder

### Google Colab

**Cell 1 — Install dependencies:**
```python
!pip install pandas openpyxl thefuzz
```

**Cell 2 — Create folders:**
```python
import os
os.makedirs("/content/nielsen/input", exist_ok=True)
os.makedirs("/content/nielsen/output", exist_ok=True)
print("Folders created")
```

**Cell 3 — Upload input Excel files:**
```python
from google.colab import files
import shutil

uploaded = files.upload()
for filename in uploaded.keys():
    shutil.move(filename, f"/content/nielsen/input/{filename}")
    print(f"Moved: {filename}")
```

Upload these files:
- Source Excel file (e.g. `Lozenge Hotsheet.xlsx`)
- `Output_Template.xlsx`
- If two source files: the second file as well (e.g. `Sanitizer Hotsheet - Remaining.xlsx`)

**Cell 4 — Upload Python files:**
```python
uploaded = files.upload()
for filename in uploaded.keys():
    shutil.move(filename, f"/content/nielsen/{filename}")
    print(f"Moved: {filename}")
```

Upload these 6 files: `config.py`, `loader.py`, `transformer.py`, `validation.py`, `writer.py`, `main.py`

**Cell 5 — Verify and update paths in config.py for Colab:**
```python
# Check current path lines
with open("/content/nielsen/config.py", "r") as f:
    content = f.read()

for line in content.split("\n"):
    if "INPUT_DIR" in line or "OUTPUT_DIR" in line:
        print(repr(line))
```

Once you see the exact spacing, run:
```python
with open("/content/nielsen/config.py", "r") as f:
    content = f.read()

content = content.replace(
    'INPUT_DIR    = "input"',
    'INPUT_DIR    = "/content/nielsen/input"'
)
content = content.replace(
    'OUTPUT_DIR   = "output"',
    'OUTPUT_DIR   = "/content/nielsen/output"'
)

with open("/content/nielsen/config.py", "w") as f:
    f.write(content)

# Verify the change worked
with open("/content/nielsen/config.py", "r") as f:
    for line in f.read().split("\n"):
        if "INPUT_DIR" in line or "OUTPUT_DIR" in line:
            print(line)
```

You should see:
```
INPUT_DIR    = "/content/nielsen/input"
OUTPUT_DIR   = "/content/nielsen/output"
```

**Cell 6 — Run the pipeline:**
```python
import sys

# Clear any cached imports
for mod in ["config", "loader", "transformer", "validation", "writer", "main"]:
    if mod in sys.modules:
        del sys.modules[mod]

sys.path.append("/content/nielsen")
from main import main
main()
```

**Cell 7 — Download output:**
```python
from google.colab import files
files.download("/content/nielsen/output/Output_Lozenge.xlsx")
```

Change `Output_Lozenge.xlsx` to match the `CATEGORY_NAME` set in `config.py`.

---

## What the Analyst Updates

### Every month (same category)

| What | Where | Example — April to May |
|---|---|---|
| `Mth_CY` and `Mth_PY` | `config.py` LONG_PERIODS | `"Apr 2026"` → `"May 2026"` |
| `L3M_CY` and `L3M_PY` | `config.py` LONG_PERIODS | `"L3M Apr 2026"` → `"L3M May 2026"` |
| `YTD_CY` and `YTD_PY` | `config.py` LONG_PERIODS | `"YTD Apr 2026"` → `"YTD May 2026"` |
| `MAT_CY` and `MAT_PY` | `config.py` LONG_PERIODS | `"MAT Apr 2026"` → `"MAT May 2026"` |
| `L6M_MONTHS_CY` | `config.py` | Remove oldest month, add newest |
| `L6M_MONTHS_PY` | `config.py` | Remove oldest month, add newest |
| Input Excel files | `input/` folder | Drop new files, keep same filenames |

**Note:** Period updates are only needed for long-format files (e.g. Sanitizer-style). Wide-format files (e.g. Lozenge-style) use simple labels like `Mth 25`, `Mth 26` which do not change month to month.

### When switching to a new category

Only `config.py` needs to be updated. Edit these sections:

**1. File paths and category name:**
```python
CATEGORY_NAME  = "Toothpaste"
SOURCE_FILE    = f"{INPUT_DIR}/Toothpaste Hotsheet.xlsx"
HAS_SECOND_FILE = False          # Set True if two source files
SOURCE_SHEET   = "Data"          # Sheet name in source file
```

**2. Brand role names (wide format):**
```python
WIDE_ROLES = {
    "focal"      : {"brand": "COLGATE",    "level": "Brand",    "segment": "COLGATE"},
    "category"   : {"brand": "TOOTHPASTE", "level": "Category", "segment": "TOOTHPASTE"},
    "competitor" : {"brand": "SENSODYNE",  "level": "Brand",    "segment": "SENSODYNE"},
}
```

**3. Brand role names (long format):**
```python
LONG_ROLES = {
    "focal"      : {"brand_family": "COLGATE",   "product_name": "Total"},
    "category"   : {"brand_family": "Total",     "product_name": "Total"},
    "competitor" : {"brand_family": "SENSODYNE", "product_name": "Total"},
}
```

**4. Template sheet name:**
```python
TEMPLATE_SHEET = "Colgate"
```

**5. Period column names (long format only):**
```python
LONG_PERIODS = {
    "Mth_PY": "Apr 2025", "Mth_CY": "Apr 2026",
    "L3M_PY": "L3M Apr 2025", "L3M_CY": "L3M Apr 2026",
    "YTD_PY": "YTD Apr 2025", "YTD_CY": "YTD Apr 2026",
    "MAT_PY": "MAT Apr 2025", "MAT_CY": "MAT Apr 2026",
}
L6M_MONTHS_CY = ["Nov 2025","Dec 2025","Jan 2026","Feb 2026","Mar 2026","Apr 2026"]
L6M_MONTHS_PY = ["Nov 2024","Dec 2024","Jan 2025","Feb 2025","Mar 2025","Apr 2025"]
```

**6. Geography mappings** — only if the new category covers different geographies:
```python
WIDE_GEO_MAP = {
    "INDIA (U+R)" : "All India (Total)",
    # Add or remove as needed
}
```

### What never needs to be updated

- `loader.py` — never touch
- `transformer.py` — never touch
- `validation.py` — never touch
- `writer.py` — never touch
- `main.py` — never touch

---

## Module Overview

**`config.py`**
The only file edited between runs. Contains all file paths, sheet names, column mappings, brand role definitions, geography mappings, period column names and template coordinates. Everything the analyst might need to change lives here.

**`loader.py`**
Loads the source Excel file(s) into DataFrames. Auto-detects wide vs long format. Validates that all expected columns exist before reading any data — fails loudly if columns are missing or renamed. Applies fuzzy geography matching to catch minor spelling differences. Merges two files when HAS_SECOND_FILE is True, with the first file taking priority for any overlapping geography.

**`transformer.py`**
Extracts specific values from the loaded DataFrame by role, geography, metric and time period. For wide-format files, applies the `Product == Segment` structural rule to isolate the correct brand-level row. For long-format files, derives L6M by summing 6 monthly columns for additive metrics and averaging for non-additive metrics. Warns if any filter returns zero or more than one row.

**`validation.py`**
Cross-checks the pre-built MAT column against the sum of 12 individual monthly columns for key brand and geography combinations. Validates within 1% tolerance. Prints derived value, reported value and percentage difference for any mismatch. Runs for long-format files only.

**`writer.py`**
Copies the Output Template and populates it with extracted values. Uses dynamic template reading to locate geography rows and metric columns by their labels rather than fixed coordinates. Computes and logs growth between current year and prior year for key metrics at All India level. Growth is not written to the template but printed in the run log for reference.

**`main.py`**
Orchestrates the full pipeline in order: load → validate → extract → write. Running `python main.py` executes all steps and produces the populated output file.

---

## Configuration Reference

| Setting | What it controls | Update when |
|---|---|---|
| `CATEGORY_NAME` | Output file name | New category |
| `SOURCE_FILE` | Path to source Excel file | New category or file renamed |
| `HAS_SECOND_FILE` | Whether to load a second file | New category |
| `SOURCE_FILE_2` | Path to second source file | New category with two files |
| `SOURCE_SHEET` | Sheet name in source file | New category |
| `WIDE_ROLES` | Brand names for wide-format files | New category |
| `LONG_ROLES` | Brand names for long-format files | New category |
| `WIDE_PERIODS` | Period column names for wide files | Rarely — labels are stable |
| `LONG_PERIODS` | Period column names for long files | Every month |
| `L6M_MONTHS_CY` | 6 CY monthly columns for L6M | Every month |
| `L6M_MONTHS_PY` | 6 PY monthly columns for L6M | Every month |
| `TEMPLATE_SHEET` | Sheet name in output template | New category |
| `WIDE_GEO_MAP` | Geography mapping for wide files | New geographies |
| `LONG_GEO_MAP` | Geography mapping for long files | New geographies |
| `METRIC_NAMES` | Metric column name mappings | Column names change in source |
| `BLOCK_STARTS` | Template column positions | Template structure changes |
| `TEMPLATE_GEO_ROWS` | Template row positions | Template structure changes |

---

## Output

`Output_{CategoryName}.xlsx` is saved in the `output/` folder. It contains one populated sheet with:

- **12 geography rows** — All India through Maharashtra (rows 7–18)
- **13 metric blocks** — 5 focal brand metrics, 3 category metrics, 5 competitor metrics
- **10 columns per block** — Mth 25, Mth 26, L3M 25, L3M 26, L6M 25, L6M 26, YTD 25, YTD 26, MAT 25, MAT 26

Geographies absent from the source file are left blank — this is correct behaviour, not an error.

---

## Validation Output

The pipeline prints a validation summary during the run:

```
============================================================
RUNNING MAT CROSS-VALIDATION (Long Format)
============================================================
  ✓ PASS — focal (DETTOL) All India (diff: 0.12%)
  ✓ PASS — category (Total) All India (diff: 0.08%)
  ✓ PASS — competitor (LIFEBUOY) All India (diff: 0.21%)

  Summary: 3 passed, 0 mismatches
============================================================
```

MAT mismatches above 1% are flagged with derived value, reported value and percentage difference. MAT validation runs for long-format files only.

---

## Known Limitations

- Period column names for long-format files must be manually updated every month. This is the primary difference from Format 2, which auto-detects these.
- Geography mappings require manual configuration. Fuzzy matching catches minor spelling differences (threshold: 90/100) but significant changes require a config update.
- The output template structure is configured manually. Dynamic template reading handles minor row or column shifts but not a fundamental restructuring.
- Header row positions are configured manually in `config.py`. Auto-detection of header rows is not implemented.
- Brand names are manually configured — they are a business decision that cannot be inferred from the data.

---

## Assumptions

- **Brand row selection (wide format):** The row where `Segment == Product` identifies the brand-level total. This is the structural rule Nielsen uses in wide-format exports to distinguish brand totals from segment or variant rows. The file does not contain an explicit overall brand total row — this rule is applied consistently across all brands and geographies.
- **L6M aggregation:** Sales Value and Units are summed across 6 months. MS Val%, Store Count and WD% are averaged — they are ratios or point-in-time counts, not additive flows. Deviation analysis was performed to validate this choice — Store Count and WD% show outlier months that can skew the average; median would be more robust but simple average is used as a reasonable approximation.
- **Sanitizer overlap rule:** Where the same geography appears in both source files, the first file takes priority. This is logged during every run.
- **Data accuracy:** Source data is assumed accurate as received. No error analysis is performed on the underlying values.
- **MS Val% index values:** Values exceeding 100% in long-format files are treated as index values rather than traditional market share percentages. They are used directionally rather than as absolute share figures.
- **Output template structure:** The writer assumes the template maintains its current row and column structure between runs. Dynamic template reading handles minor shifts but not fundamental restructuring.
