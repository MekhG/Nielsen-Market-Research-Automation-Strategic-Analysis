#CHECK 12: MAT validation test:
## Cross-check the pre-built MAT column against the sum of 12 monthly columns for key brand and
## geography combinations. Confirms the agency-reported MAT values are internally consistent with the monthly data.

import sys
for mod in ["validation"]:
    if mod in sys.modules:
        del sys.modules[mod]

sys.path.append("/content/nielsen")
from validation import run_all_validations

run_all_validations(df_san)
