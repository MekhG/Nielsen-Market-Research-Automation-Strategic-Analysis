# Nielsen Market Research Automation & Strategic Analysis

A Python pipeline that reads raw Nielsen market research Excel exports, consolidates them into a fixed reporting template, and provides a structured strategic analysis framework for commercial decision-making.

---

## Project Structure

```
nielsen_automation/
│
├── input/                          # Drop source Excel files here
├── output/                         # Output_Filled.xlsx is generated here
│
├── config.py                       # All changeable parameters — only file edited monthly
├── loader.py                       # Reads and validates source files, merges Sanitizer files
├── transformer.py                  # Extracts values by role, geography, metric and period
├── validation.py                   # Cross-checks MAT against monthly columns
├── writer.py                       # Populates Output Template, logs growth figures
├── main.py                         # Orchestrates the full pipeline
└── requirements.txt                # Python dependencies
```

---

## Demo Files

Four demonstration files are included with fictional brand names to allow the pipeline to be tested without using proprietary Nielsen data. The file structure, column names, geography hierarchy, metric names and numeric value ranges are identical to the real files.


**Files:**
- `Lozenge Hotsheet.xlsx` — wide format, sheet `Cat x Brand x Seg`
- `Sanitizer Hotsheet.xlsx` — long format, sheet `Brands` (main geographies)
- `Sanitizer Hotsheet - Remaining.xlsx` — long format, sheet `Brands` (additional geographies)
- `Output_Template.xlsx` — two sheets: `Zestol` and `Clearo`

To run the pipeline on the demo files, update the brand role names in `config.py` as described in the Configuration section below.

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

### Local (Jupyter Notebook, VS Code, terminal)

1. Place all four input Excel files in the `input/` folder
2. Update period column names in `config.py` (see Monthly Updates below)
3. Run:

```bash
python main.py
```

4. Find `Output_Filled.xlsx` in the `output/` folder

### Google Colab

```python
# Install dependencies
!pip install pandas openpyxl thefuzz

# Create folders
import os
os.makedirs("/content/nielsen/input", exist_ok=True)
os.makedirs("/content/nielsen/output", exist_ok=True)

# Upload files
from google.colab import files
import shutil
uploaded = files.upload()
for filename in uploaded.keys():
    shutil.move(filename, f"/content/nielsen/input/{filename}")

# Run pipeline
import sys
sys.path.append("/content/nielsen")
from main import main
main()

# Download output
files.download("/content/nielsen/output/Output_Filled.xlsx")
```

---

## Module Overview

**`config.py`**
The only file that needs to be edited between monthly runs. Contains all file paths, sheet names, header row positions, column name mappings, metric names, period column names, brand role definitions, geography mappings and output template coordinates.

**`loader.py`**
Loads the Lozenge and Sanitizer Excel files into pandas DataFrames. Validates that all expected columns exist before reading any data — fails with a clear error message if columns are missing or renamed. Applies fuzzy matching to geography names to catch minor spelling or capitalisation differences between monthly files. Merges the two Sanitizer files with an explicit overlap rule: the main file takes priority for any geography appearing in both. Validates that both Sanitizer files have identical column structures before merging.

**`transformer.py`**
Extracts specific values from the loaded DataFrames by role (focal brand, category, competitor), geography, metric and time period. For the Lozenge file, applies the `Product == Segment` structural rule to isolate the correct brand-level row and avoid silent double-counting. For the Sanitizer file, derives L6M by summing 6 monthly columns for additive metrics (Sales Value, Sales Units) and averaging for non-additive metrics (MS Val%, Store Count, WD%). Raises a warning if any filter returns zero or more than one row.

**`validation.py`**
Cross-checks the pre-built MAT column against the sum of 12 individual monthly columns for key brand and geography combinations. Validates within 1% tolerance to allow for rounding. Prints the derived value, reported value and percentage difference for any mismatch so the analyst can investigate before the output is written.

**`writer.py`**
Copies the Output Template and populates the Strepsils/Zestol sheet with Lozenge data and the Dettol/Clearo sheet with Sanitizer data. Uses dynamic template reading to locate geography rows and metric columns by their labels rather than fixed coordinates — making the writer resilient to minor structural changes in the template. Computes and logs growth between current year and prior year for key metrics at All India level: percentage point change for MS Val%, percentage growth for all other metrics.

**`main.py`**
Orchestrates the full pipeline in order: load → validate → extract → write. Running `python main.py` executes all steps and produces the populated output file.

---

## What the Analyst Updates Each Month

Only `config.py` needs to be edited. Update the following:

| What | Where | Example — April to May |
|---|---|---|
| `Mth_CY` and `Mth_PY` | `config.py` | `"Apr 2026"` → `"May 2026"` |
| `L3M_CY` and `L3M_PY` | `config.py` | `"L3M Apr 2026"` → `"L3M May 2026"` |
| `YTD_CY` and `YTD_PY` | `config.py` | `"YTD Apr 2026"` → `"YTD May 2026"` |
| `MAT_CY` and `MAT_PY` | `config.py` | `"MAT Apr 2026"` → `"MAT May 2026"` |
| `L6M_MONTHS_CY` | `config.py` | Remove oldest month, add new month |
| `L6M_MONTHS_PY` | `config.py` | Remove oldest month, add new month |
| Input Excel files | `input/` folder | Drop new files, keep same filenames |

---

## Configuration

### Adapting to new brand or file names

If the source files are renamed, update these lines in `config.py`:

```python
LOZENGE_FILE             = f"{INPUT_DIR}/Lozenge Hotsheet.xlsx"
SANITIZER_MAIN_FILE      = f"{INPUT_DIR}/Sanitizer Hotsheet.xlsx"
SANITIZER_REMAINING_FILE = f"{INPUT_DIR}/Sanitizer Hotsheet - Remaining.xlsx"
```

If the brand names change, update the role definitions:

```python
# Lozenge roles
LOZENGE_ROLES = {
    "focal"      : {"brand": "ZESTOL",       "level": "Brand",    "segment": "ZESTOL"},
    "category"   : {"brand": "THROAT DROPS", "level": "Category", "segment": "THROAT DROPS"},
    "competitor" : {"brand": "MINTEX",        "level": "Brand",    "segment": "MINTEX"},
}

# Sanitizer roles
SANITIZER_ROLES = {
    "focal"      : {"brand_family": "CLEARO",     "product_name": "Total"},
    "category"   : {"brand_family": "Total",      "product_name": "Total"},
    "competitor" : {"brand_family": "PURESHIELD", "product_name": "Total"},
}

# Output template sheet names
TEMPLATE_SHEET = "Zestol"
TEMPLATE_SHEET = "Clearo"
```

### Running locally vs Colab

For local runs, use relative paths in `config.py`:

```python
INPUT_DIR  = "input"
OUTPUT_DIR = "output"
```

For Colab runs, use absolute paths:

```python
INPUT_DIR  = "/content/nielsen/input"
OUTPUT_DIR = "/content/nielsen/output"
```

---

## Output

`Output_Filled.xlsx` contains two sheets — one per brand. Each sheet has the same structure:

**Rows:** 12 geography rows (All India → Maharashtra) starting at row 7

**Columns:** 13 metric blocks, each 10 columns wide (5 periods × 2 years):

| Block | Role | Metric |
|---|---|---|
| 1 | Focal Brand | Sales Value (Cr) |
| 2 | Focal Brand | Sales Units (Mn) |
| 3 | Focal Brand | MS Val % |
| 4 | Focal Brand | Store Count (000) |
| 5 | Focal Brand | WD % |
| 6 | Category | Sales Value (Cr) |
| 7 | Category | Sales Units (Mn) |
| 8 | Category | Store Count (000) |
| 9 | Competitor | Sales Value (Cr) |
| 10 | Competitor | Sales Units (Mn) |
| 11 | Competitor | MS Val % |
| 12 | Competitor | Store Count (000) |
| 13 | Competitor | WD % |

Within each block, columns follow this order: Mth 25, Mth 26, L3M 25, L3M 26, L6M 25, L6M 26, YTD 25, YTD 26, MAT 25, MAT 26.

**Note:** East Zone, West Bengal, West Zone, Gujarat and Maharashtra are not present in the Lozenge source file. These rows are left blank in the Zestol sheet. This is a known source data limitation, not a code error.

---

## Strategic Analysis Framework

The output dataset supports two analytical frameworks for commercial decision-making.

### 1. Market Dynamics Grid

A 2×2 performance matrix that plots geographies based on two vectors:

**X axis — Category Growth %**
Whether the overall product category is growing or shrinking in a geography. Calculated as:
```
Category Growth % = ((Category MAT 26 - Category MAT 25) / Category MAT 25) × 100
```
Geographies are split into High Growth and Low Growth using the median category growth rate as the dividing line.

**Y axis — MS Val% Change**
Whether the focal brand is gaining or losing market share against the named competitor. Calculated as:
```
MS Val% Change = MS Val% MAT 26 - MS Val% MAT 25   (expressed in percentage points, pp)
```
Positive = gaining share. Negative = losing share. Dividing line = 0pp.

**MAT is used as the primary axis for plotting.** YTD is shown alongside as a directional indicator — whether the MAT trend is improving, worsening or reversing in the current year. This combination shows both where a geography stands historically and where it is heading.

**Four quadrants:**

| | Low Category Growth | High Category Growth |
|---|---|---|
| **MS Gaining** | Defend and Extract | Core to Defend |
| **MS Losing** | Intervention Needed | Opportunity to Capture |

---

### 2. Push vs Pull Diagnostic Framework

A 2×2 matrix that diagnoses why a geography is underperforming — whether the cause is a distribution failure (retail push) or a demand failure (consumer pull).

**X axis — Store Count MAT Change %**
Whether numeric distribution (number of stores stocking the brand) is growing or declining.

**Y axis — Velocity MAT Change %**
Velocity = Sales Value ÷ Store Count. Whether the brand is generating more or less revenue per store — a proxy for consumer demand at the point of sale.

**Four quadrants:**

| | Store Count Declining | Store Count Growing |
|---|---|---|
| **Velocity Growing** | Push Problem — demand intact, retail presence failing | Star — both distribution and demand working |
| **Velocity Declining** | Dual Problem — both distribution and demand failing | Pull Problem — stores available but consumers not buying |

**Interpreting Push vs Pull:**
- **Push Problem** → invest in trade incentives, distributor activation, shelf recovery
- **Pull Problem** → invest in consumer marketing, promotions, sampling, pricing review
- **Dual Problem** → requires both trade and consumer intervention
- **Star** → protect and accelerate investment

**Note on WD% vs Store Count:** Store Count (numeric distribution) and WD% (weighted distribution) can tell different stories. A brand can lose many low-volume stores (Store Count falls sharply) while WD% barely moves if the lost stores were small outlets. Both metrics should be checked together — Store Count gives the headline retail reach picture, WD% gives the value-weighted distribution picture. Where they diverge, WD% is the more commercially relevant signal.

---

### 3. Commercial Recommendation Framework

Findings from the Market Dynamics Grid and Push vs Pull matrix feed directly into budget allocation decisions:

| Diagnosis | Type of Spend |
|---|---|
| Distribution Problem (Push) | Trade spend — retailer incentives, distributor activation, shelf fees |
| Demand Problem (Pull) | Consumer spend — advertising, promotions, sampling, pricing |
| Dual Problem | Split between trade and consumer activation |
| Star geography | Maintenance and acceleration spend |

Recommendations should always cite specific data points, for example: *"Allocate trade spend to Zone X because Store Count declined -54% MAT while velocity per store rose +133%, confirming a distribution problem not a demand problem."* Generic statements without data evidence are not sufficient.

---

## Sample Analysis Output

The following matrices were generated by running the pipeline on the fake demo files (ZESTOL and CLEARO). All values are derived from randomly generated demo data — they illustrate the analytical output format, not real market performance.

---

### Market Dynamics Grid — ZESTOL (Lozenge Hotsheet)

**Median Category MAT Growth = +7.7% (used as High/Low dividing line)**
**MS Val% Change dividing line = 0pp**

```
┌─────────────────────────────────────┬─────────────────────────────────────┐
│                                     │                                     │
│   LOW GROWTH                        │   HIGH GROWTH                       │
│   MS GAINING                        │   MS GAINING                        │
│                                     │                                     │
│   North Zone                        │   All India (Total)                 │
│   Cat MAT: -14.0% | YTD: +5.2%      │   Cat MAT: +14.4% | YTD: +16.0%   │
│   MS MAT:  +5.84pp | YTD: -4.52pp ▼ │   MS MAT:  +3.29pp | YTD: -4.27pp ▼│
│                                     │                                     │
│   Delhi                             │   Tamil Nadu                        │
│   Cat MAT:  -1.8% | YTD: -15.1%    │   Cat MAT:  +7.7% | YTD: -7.8%    │
│   MS MAT:  +2.34pp | YTD: -6.18pp ▼│   MS MAT:  +8.23pp | YTD: +2.66pp ▲│
│                                     │                                     │
├─────────────────────────────────────┼─────────────────────────────────────┤
│                                     │                                     │
│   LOW GROWTH                        │   HIGH GROWTH                       │
│   MS LOSING                         │   MS LOSING                         │
│                                     │                                     │
│   Punjab                            │   South Zone                        │
│   Cat MAT:  +2.2% | YTD: +5.6%     │   Cat MAT: +13.1% | YTD: -8.0%    │
│   MS MAT:  -8.03pp | YTD: +7.05pp ▲│   MS MAT:  -7.31pp | YTD: +12.41pp▲│
│                                     │                                     │
│                                     │   Karnataka                         │
│                                     │   Cat MAT: +16.6% | YTD: +4.2%    │
│                                     │   MS MAT:  -3.24pp | YTD: -5.92pp ▼│
│                                     │                                     │
└─────────────────────────────────────┴─────────────────────────────────────┘
          Cat Growth < +7.7% (Low)            Cat Growth ≥ +7.7% (High)
```

**Summary Table:**

| Geography | Cat MAT | Cat YTD | MS MAT | MS YTD | Quadrant |
|---|---|---|---|---|---|
| All India (Total) | +14.4% | +16.0% | +3.29pp | -4.27pp ▼ | High Growth + MS Gaining |
| North Zone | -14.0% | +5.2% | +5.84pp | -4.52pp ▼ | Low Growth + MS Gaining |
| Delhi | -1.8% | -15.1% | +2.34pp | -6.18pp ▼ | Low Growth + MS Gaining |
| Punjab | +2.2% | +5.6% | -8.03pp | +7.05pp ▲ | Low Growth + MS Losing |
| South Zone | +13.1% | -8.0% | -7.31pp | +12.41pp ▲ | High Growth + MS Losing |
| Karnataka | +16.6% | +4.2% | -3.24pp | -5.92pp ▼ | High Growth + MS Losing |
| Tamil Nadu | +7.7% | -7.8% | +8.23pp | +2.66pp ▲ | High Growth + MS Gaining |

▲ = YTD trend improving | ▼ = YTD trend worsening

---

### Market Dynamics Grid — CLEARO (Sanitizer Hotsheet)

**Median Category MAT Growth = -2.5% (used as High/Low dividing line)**
**MS Val% Change dividing line = 0pp**

```
┌─────────────────────────────────────┬─────────────────────────────────────┐
│                                     │                                     │
│   LOW GROWTH                        │   HIGH GROWTH                       │
│   MS GAINING                        │   MS GAINING                        │
│                                     │                                     │
│   All India (Total)                 │   Karnataka                         │
│   Cat MAT: -49.8% | YTD: -30.0%    │   Cat MAT:  +1.0% | YTD: +28.6%   │
│   MS MAT:  +2.19pp | YTD: -0.97pp ▼│   MS MAT:  +7.39pp | YTD: +32.78pp▲│
│                                     │                                     │
│   North Zone                        │   Tamil Nadu                        │
│   Cat MAT: -14.6% | YTD: +144.8%   │   Cat MAT: +31.1% | YTD: +111.2%  │
│   MS MAT: +22.24pp | YTD: +19.69pp▲│   MS MAT: +11.19pp | YTD: -23.74pp▼│
│                                     │                                     │
│   Delhi                             │   Maharashtra                       │
│   Cat MAT: -29.1% | YTD: -36.1%    │   Cat MAT:  -0.8% | YTD: +51.6%   │
│   MS MAT:  +0.75pp | YTD: -17.68pp▼│   MS MAT: +21.13pp | YTD: +6.50pp ▲│
│                                     │                                     │
│                                     │   West Bengal                       │
│                                     │   Cat MAT:  +1.7% | YTD: -6.2%    │
│                                     │   MS MAT: -25.40pp | YTD: +0.86pp ▲│
│                                     │                                     │
│                                     │   East Zone                         │
│                                     │   Cat MAT:  +0.5% | YTD: -4.1%    │
│                                     │   MS MAT:  -9.23pp | YTD: -26.54pp▼│
│                                     │                                     │
├─────────────────────────────────────┼─────────────────────────────────────┤
│                                     │                                     │
│   LOW GROWTH                        │   HIGH GROWTH                       │
│   MS LOSING                         │   MS LOSING                         │
│                                     │                                     │
│   West Zone                         │   South Zone                        │
│   Cat MAT: -24.9% | YTD: -57.4%    │   Cat MAT: +25.0% | YTD: +99.3%   │
│   MS MAT: -24.59pp | YTD: -21.08pp▼│   MS MAT:  -7.33pp | YTD: -27.05pp▼│
│                                     │                                     │
│   Punjab                            │                                     │
│   Cat MAT: -12.5% | YTD: -46.8%    │                                     │
│   MS MAT:  -8.69pp | YTD: -3.66pp ▼│                                     │
│                                     │                                     │
│   Gujarat                           │                                     │
│   Cat MAT:  -4.2% | YTD: +50.3%    │                                     │
│   MS MAT:  -4.04pp | YTD: +22.21pp▲│                                     │
│                                     │                                     │
└─────────────────────────────────────┴─────────────────────────────────────┘
          Cat Growth < -2.5% (Low)            Cat Growth ≥ -2.5% (High)
```

**Summary Table:**

| Geography | Cat MAT | Cat YTD | MS MAT | MS YTD | Quadrant |
|---|---|---|---|---|---|
| All India (Total) | -49.8% | -30.0% | +2.19pp | -0.97pp ▼ | Low Growth + MS Gaining |
| North Zone | -14.6% | +144.8% | +22.24pp | +19.69pp ▲ | Low Growth + MS Gaining |
| South Zone | +25.0% | +99.3% | -7.33pp | -27.05pp ▼ | High Growth + MS Losing |
| East Zone | +0.5% | -4.1% | -9.23pp | -26.54pp ▼ | High Growth + MS Losing |
| West Zone | -24.9% | -57.4% | -24.59pp | -21.08pp ▼ | Low Growth + MS Losing |
| Delhi | -29.1% | -36.1% | +0.75pp | -17.68pp ▼ | Low Growth + MS Gaining |
| Punjab | -12.5% | -46.8% | -8.69pp | -3.66pp ▼ | Low Growth + MS Losing |
| Karnataka | +1.0% | +28.6% | +7.39pp | +32.78pp ▲ | High Growth + MS Gaining |
| Tamil Nadu | +31.1% | +111.2% | +11.19pp | -23.74pp ▼ | High Growth + MS Gaining |
| West Bengal | +1.7% | -6.2% | -25.40pp | +0.86pp ▲ | High Growth + MS Losing |
| Gujarat | -4.2% | +50.3% | -4.04pp | +22.21pp ▲ | Low Growth + MS Losing |
| Maharashtra | -0.8% | +51.6% | +21.13pp | +6.50pp ▲ | High Growth + MS Gaining |

▲ = YTD trend improving | ▼ = YTD trend worsening

---

### Push vs Pull Diagnostic Matrix

The Push vs Pull matrix is applied to a specific underperforming geography after the Market Dynamics Grid identifies where to look. The example below shows the matrix structure using illustrative quadrant labels — actual values are computed from the output file for the chosen geography.

```
┌─────────────────────────────────────┬─────────────────────────────────────┐
│                                     │                                     │
│   PUSH PROBLEM                      │   STAR                              │
│   Demand strong,                    │   Distribution growing +            │
VELOCITY    │   stores declining                  │   velocity growing                  │
GROWING (+) │                                     │                                     │
            │   → Trade spend:                    │   → Protect and                     │
            │     retailer activation,            │     accelerate investment            │
            │     shelf recovery                  │                                     │
            │                                     │                                     │
────────────┼─────────────────────────────────────┼─────────────────────────────────────
            │                                     │                                     │
VELOCITY    │   DUAL PROBLEM                      │   PULL PROBLEM                      │
DECLINING(-)│   Both distribution                 │   Stores growing,                   │
            │   and demand failing                │   velocity declining                │
            │                                     │                                     │
            │   → Split trade +                   │   → Consumer marketing:             │
            │     consumer spend                  │     promotions, sampling,           │
            │                                     │     pricing review                  │
            │                                     │                                     │
└─────────────────────────────────────┴─────────────────────────────────────┘
        Store Count Declining (-)             Store Count Growing (+)
                   ◄──────────────────────────────────────►
                            DISTRIBUTION (PUSH)
```

**Velocity = Sales Value ÷ Store Count** — a proxy for consumer demand at the point of sale. Rising velocity with declining store count confirms a Push/distribution problem. Declining velocity with stable or growing store count confirms a Pull/demand problem.

**Note:** WD% (weighted distribution) should always be checked alongside Store Count. Store Count and WD% can diverge when the stores lost are low-volume outlets — WD% barely moves while Store Count falls sharply. Where they diverge, WD% is the more commercially relevant signal.

---

## Known Limitations

- The script will not work if input files have significantly different column names from what is configured in `config.py`. The validation step catches missing columns and alerts the analyst, but cannot automatically adapt to renamed columns.
- The script will not work if the Output Template structure changes significantly. Dynamic template reading handles minor row or column shifts but not a fundamental restructuring.
- L6M for Store Count and WD% uses simple average across 6 months. Outlier months can skew the average — median would be a more robust aggregation method.
- Header row positions are configured manually in `config.py`. Auto-detection of header rows is not implemented.
- Period column names must be updated manually in `config.py` each month. Auto-detection of the latest month from the file is not implemented.
- If both Sanitizer files develop different column structures in future, the merge validation will catch it and stop the pipeline — but the analyst must resolve the structural difference manually.

---

## Assumptions

- **Brand row selection (Lozenge):** The row where `Segment == Product` (e.g. ZESTOL/ZESTOL) is treated as the brand-level total. Segment rows like CLASSIC and BERRY represent the brand's performance within different category segments — not flavour variants of one product. Summing them would inflate figures and produce market share values exceeding 100%.
- **L6M aggregation:** Sales Value and Units are summed across 6 months. MS Val%, Store Count and WD% are averaged across 6 months as they are ratios or point-in-time counts, not additive flows.
- **Sanitizer overlap rule:** Both Sanitizer files contain an ALL INDIA row. The main file takes priority — ALL INDIA rows from the Remaining file are dropped before combining. This is logged during every run.
- **Competitor identification:** The competitor for each brand is configured in `config.py` and taken from the reporting brief. It is not calculated or discovered from the data.
- **Manufacturer filter:** The Sanitizer file's Manufacturer column is not used as a filter. Brand Family and Product Name together are considered sufficient to identify the correct rows.
- **MS Val% index values:** In the Sanitizer file, MS Val% figures for some geographies exceed 100%. These are treated as index values rather than traditional market share percentages, a known characteristic of certain Nielsen export formats. They are used directionally (change in value) rather than as absolute share figures.
- **Data accuracy:** Source data is assumed accurate as received from the agency. No error analysis is performed on the underlying values.
- **Latest month:** April 2026 is the latest available month across all source files. All period references are anchored to this month.
- **Output Template structure:** The writer assumes the template maintains its current row and column structure between monthly runs.
