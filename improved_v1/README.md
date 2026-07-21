Format 1 — Single Category, Config-Driven Pipeline

Format 1 automates the population of a Nielsen reporting template for one product category at a time. Given one or two raw Nielsen Excel files (e.g. a Lozenge Hotsheet or a Sanitizer Hotsheet), it reads the source data, extracts the correct values for three roles (focal brand, category total, competitor) across all geographies, metrics and time periods, and writes them into the correct cells of the output template.

The key improvement over the original pipeline is format auto-detection, the code automatically identifies whether the source file is in wide format (one row per brand × geography × metric, like the Lozenge file) or long format (metrics stacked in a single column, like the Sanitizer file). The analyst does not need to specify the format manually.

To switch to a new category (e.g. Toothpaste next month), the analyst updates only config.py, changing the file name, brand names, sheet name and period column names. All logic files stay untouched. The output is saved as Output_{CategoryName}.xlsx so each category produces its own clearly named file.

Requirements:

Install dependencies

python
!pip install pandas openpyxl thefuzz

Create folders

python
import os
os.makedirs("/content/nielsen/input", exist_ok=True)
os.makedirs("/content/nielsen/output", exist_ok=True)
print("Folders created")

Upload input files
python
from google.colab import files
import shutil
uploaded = files.upload()
for filename in uploaded.keys():
    shutil.move(filename, f"/content/nielsen/input/{filename}")
    print(f"Moved: {filename}")

Upload the Python files
python
uploaded = files.upload()
for filename in uploaded.keys():
    shutil.move(filename, f"/content/nielsen/{filename}")
    print(f"Moved: {filename}")

Update paths in config.py for Colab
python
# Directly overwrite just the path lines in config.py
with open("/content/nielsen/config.py", "r") as f:
    content = f.read()

# Print current path lines so we can see what needs changing
for line in content.split("\n"):
    if "INPUT_DIR" in line or "OUTPUT_DIR" in line:
        print(repr(line))

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
            
Run the pipeline
import sys
sys.path.append("/content/nielsen")

# Clear any cached imports
for mod in ["config", "loader", "transformer", "validation", "writer", "main"]:
    if mod in sys.modules:
        del sys.modules[mod]

from main import main
main()

Download output
python
from google.colab import files
files.download("/content/nielsen/output/Output_Lozenge.xlsx")
