# Nielsen Market Research Automation — Format 2
## Hands-Off Auto-Detection Pipeline

Format 2 is the most automated version of the Nielsen Market Research Automation Pipeline. It builds on Format 1 by eliminating the need to manually update period column names each month. Drop in new files and run — the pipeline figures out the rest.

---

## What is New in Format 2

### Compared to the Original Pipeline (v1/v2 notebooks)

| Area | Original | Format 2 |
|---|---|---|
| Period column names | Manually updated every month in config.py | Auto-detected from file column names |
| L6M month list | Manually updated every month in config.py | Auto-detected as 6 most recent monthly columns |
| File format | Manually specified in config.py | Auto-detected by checking if Metric column exists |
| Monthly update effort | 6+ config lines to change every month | Drop files and run — nothing to change |
| Two-file merge | Supported | Supported |
| MAT cross-validation | Manual month list | Auto-detected monthly columns |

### Compared to Format 1

| Area | Format 1 | Format 2 |
|---|---|---|
| Period column names | Manually configured in WIDE_PERIODS / LONG_PERIODS | Auto-detected from file |
| L6M months | Manually configured in L6M_MONTHS_CY / L6M_MONTHS_PY | Auto-detected from file |
| Monthly update effort | Update 6 period-related lines in config.py | Nothing — just drop new files |
| New file: detector.py | Not present | Added — handles all auto-detection logic |
| Config.py size | Larger — includes period dictionaries | Smaller — no period dictionaries needed |

---

## How Auto-Detection Works

Format 2 includes a dedicated module — `detector.py` — that analyses the loaded DataFrame before any extraction begins.

**For wide-format files (e.g. Lozenge-style):**
- Scans column names for patterns like `Mth 25`, `L3M 26`, `MAT 25` etc.
- Identifies the two year suffixes present (e.g. 25 and 26)
- Assigns the higher year as current year (CY) and lower as prior year (PY)
- Maps all 10 period keys automatically

**For long-format files (e.g. Sanitizer-style):**
- Scans all columns for monthly date patterns like `Apr 2026`, `Nov 2025` etc.
- Identifies the most recent month as the latest month (CY Mth)
- Derives prior year equivalent automatically (e.g. Apr 2026 → Apr 2025)
- Pattern-matches pre-built period columns: `L3M Apr 2026`, `YTD Apr 2026`, `MAT Apr 2026`
- Identifies the 6 most recent monthly columns as L6M CY months
- Identifies the same 6 months one year prior as L6M PY months

**If detection fails:**
- A clear WARNING is printed for each period that could not be detected
- The pipeline continues with whatever was successfully detected
- No silent failures — every gap is logged

---

## Project Structure

```
format2/
│
├── input/                          # Drop source Excel files here
├── output/                         # Output file is generated here
│
├── config.py                       # Analyst-facing config — minimal monthly edits
├── detector.py                     # Auto-detection engine — never edit
├── loader.py                       # File loading and validation — never edit
├── transformer.py                  # Data extraction — never edit
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

```python
# Cell 1 — Install dependencies
!pip install pandas openpyxl thefuzz

# Cell 2 — Create folders
import os
os.makedirs("/content/nielsen_f2/input", exist_ok=True)
os.makedirs("/content/nielsen_f2/output", exist_ok=True)

# Cell 3 — Upload Excel input files
from google.colab import files
import shutil
uploaded = files.upload()
for filename in uploaded.keys():
    shutil.move(filename, f"/content/nielsen_f2/input/{filename}")
    print(f"Moved: {filename}")

# Cell 4 — Upload Python files
uploaded = files.upload()
for filename in uploaded.keys():
    shutil.move(filename, f"/content/nielsen_f2/{filename}")
    print(f"Moved: {filename}")
```

Upload these 7 Python files: `config.py`, `detector.py`, `loader.py`, `transformer.py`, `validation.py`, `writer.py`, `main.py`

```python
# Cell 5 — Fix paths for Colab
with open("/content/nielsen_f2/config.py", "r") as f:
    content = f.read()
content = content.replace('INPUT_DIR     = "input"',
                          'INPUT_DIR     = "/content/nielsen_f2/input"')
content = content.replace('OUTPUT_DIR    = "output"',
                          'OUTPUT_DIR    = "/content/nielsen_f2/output"')
with open("/content/nielsen_f2/config.py", "w") as f:
    f.write(content)
print("Paths updated")

# Cell 6 — Run pipeline
import sys
for mod in ["config","detector","loader","transformer","validation","writer","main"]:
    if mod in sys.modules:
        del sys.modules[mod]
sys.path.append("/content/nielsen_f2")
from main import main
main()

# Cell 7 — Download output
from google.colab import files
files.download("/content/nielsen_f2/output/Output_Lozenge.xlsx")
```

---

## What the Analyst Updates

### Every month (same category)

| What | Action |
|---|---|
| New source Excel files | Drop into `input/` folder — nothing else |

That is it. Period names, L6M months and file format are all auto-detected.

### When switching to a new category

Only `config.py` needs to be updated. Edit these sections:

**1. File paths and category name:**
```python
CATEGORY_NAME  = "Toothpaste"   # Used to name the output file
SOURCE_FILE    = f"{INPUT_DIR}/Toothpaste Hotsheet.xlsx"
HAS_SECOND_FILE = False          # Set True if two source files
SOURCE_SHEET   = "Data"          # Sheet name in the source file
```

**2. Brand role names:**
```python
# For wide-format files:
WIDE_ROLES = {
    "focal"      : {"brand": "COLGATE",    "level": "Brand",    "segment": "COLGATE"},
    "category"   : {"brand": "TOOTHPASTE", "level": "Category", "segment": "TOOTHPASTE"},
    "competitor" : {"brand": "SENSODYNE",  "level": "Brand",    "segment": "SENSODYNE"},
}

# For long-format files:
LONG_ROLES = {
    "focal"      : {"brand_family": "COLGATE",   "product_name": "Total"},
    "category"   : {"brand_family": "Total",     "product_name": "Total"},
    "competitor" : {"brand_family": "SENSODYNE", "product_name": "Total"},
}
```

**3. Template sheet name:**
```python
TEMPLATE_SHEET = "Colgate"   # Must match sheet name in Output_Template.xlsx
```

**4. Geography mappings** — only if the new category covers different geographies:
```python
WIDE_GEO_MAP = {
    "INDIA (U+R)" : "All India (Total)",
    # Add or remove geographies as needed
}
```

### What never needs to be updated

- Period column names — auto-detected
- L6M month lists — auto-detected
- File format (wide vs long) — auto-detected
- `detector.py`, `loader.py`, `transformer.py`, `validation.py`, `writer.py`, `main.py` — never touch these

---

## Configuration Reference

### Key config.py settings

| Setting | What it controls | Update when |
|---|---|---|
| `CATEGORY_NAME` | Output file name | New category |
| `SOURCE_FILE` | Path to source Excel file | New category or file renamed |
| `HAS_SECOND_FILE` | Whether to load a second file | New category |
| `SOURCE_FILE_2` | Path to second source file | New category with two files |
| `SOURCE_SHEET` | Sheet name in source file | New category |
| `WIDE_ROLES` | Brand names for wide-format files | New category |
| `LONG_ROLES` | Brand names for long-format files | New category |
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

The pipeline prints a validation summary after loading:

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

MAT mismatches above 1% are flagged with the derived value, reported value and percentage difference so the analyst can investigate before accepting the output.

MAT validation runs for long-format files only — wide-format files have pre-built periods trusted from the agency.

---

## Known Limitations

- Geography mappings still require manual configuration in `config.py`. If a geography is spelled differently in next month's file, fuzzy matching will catch minor differences (threshold: 90/100 score) but significant changes require a config update.
- The output template structure (row and column positions) is still configured manually in `config.py`. Dynamic template reading handles minor row or column shifts but not a fundamental restructuring of the template.
- Auto-detection of the latest month assumes monthly columns follow the `Mon YYYY` pattern (e.g. `Apr 2026`). Non-standard column naming will not be detected.
- Wide-format period detection assumes year suffixes are two-digit (e.g. `25`, `26`). Four-digit years in wide-format files would not be detected.
- Brand names are still manually configured — they are a business decision that cannot be inferred from the data.

---

## Assumptions

- **Brand row selection (wide format):** The row where `Segment == Product` identifies the brand-level total. This is the structural rule Nielsen uses in wide-format exports to distinguish brand totals from segment or variant rows.
- **L6M aggregation:** Sales Value and Units are summed across 6 months. MS Val%, Store Count and WD% are averaged — they are ratios or point-in-time counts, not additive flows.
- **Latest month:** The most recent monthly column in the file is treated as the current year latest month. Prior year is set to the same month one year earlier.
- **Sanitizer overlap rule:** Where the same geography appears in both source files, the first file takes priority. This is logged during every run.
- **Data accuracy:** Source data is assumed accurate as received. No error analysis is performed on the underlying values.
- **MS Val% index values:** Values exceeding 100% in long-format files are treated as index values rather than traditional market share percentages. They are used directionally rather than as absolute share figures.
