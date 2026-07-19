## Main Execution (main.py)
##Extends main with a validation step added between loading and extraction. Pipeline now runs
## in this order: load → validate → extract → write.

%%writefile /content/nielsen/main.py
import sys
sys.path.append("/content/nielsen")

from loader import load_lozenge, load_sanitizer
from transformer import extract_lozenge_data, extract_sanitizer_data
from writer import write_output
from validation import run_all_validations

def main():
    print("=" * 60)
    print("NIELSEN AUTOMATION — STARTING")
    print("=" * 60)

    # Step 1 — Load
    df_loz = load_lozenge()
    df_san = load_sanitizer()

    # Step 2 — Validate
    run_all_validations(df_san)

    # Step 3 — Extract
    loz_data = extract_lozenge_data(df_loz)
    san_data = extract_sanitizer_data(df_san)

    # Step 4 — Write
    write_output(loz_data, san_data)

    print("=" * 60)
    print("DONE. Output file is ready.")
    print("=" * 60)

if __name__ == "__main__":
    main()
