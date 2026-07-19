##Load Data for Investigation
## Clears any cached module imports to ensure the latest version of each file is used,
## then loads the Lozenge and Sanitizer DataFrames. All subsequent investigation cells depend on this cell being run first.

import importlib
import sys

# Remove cached versions
for mod in ["loader", "transformer", "writer", "config"]:
    if mod in sys.modules:
        del sys.modules[mod]

sys.path.append("/content/nielsen")
from loader import load_lozenge, load_sanitizer

df_loz = load_lozenge()
df_san = load_sanitizer()
