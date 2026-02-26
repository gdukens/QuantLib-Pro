"""
Fix three issues:
1. Strip icon= kwarg from st.title/header/subheader (not supported in Streamlit 1.54)
2. Fix 5_Macro.py: wrong module path for correlation_regime
3. Fix 7_Backtesting.py: DataProviderFactory not in providers, move to providers_legacy
"""
import re
import glob
import os

# ── 1. Strip icon= from all pages ────────────────────────────────────────────
ICON_RE = re.compile(r',\s*icon\s*=\s*["\'][^"\']*["\']')

stripped = []
for f in sorted(glob.glob("pages/*.py")):
    src = open(f, encoding="utf-8").read()
    new = ICON_RE.sub("", src)
    if new != src:
        open(f, "w", encoding="utf-8").write(new)
        stripped.append(os.path.basename(f))

print(f"[1] Stripped icon= from {len(stripped)} files: {stripped}")

# ── 2. Fix 5_Macro.py import ─────────────────────────────────────────────────
macro_path = "pages/5_Macro.py"
src = open(macro_path, encoding="utf-8").read()
old = "from quantlib_pro.macro.correlation_regime import correlation_regime"
new = "from quantlib_pro.macro.correlation import correlation_regime"
if old in src:
    open(macro_path, "w", encoding="utf-8").write(src.replace(old, new))
    print(f"[2] Fixed correlation_regime import in {macro_path}")
else:
    print(f"[2] Pattern not found in {macro_path} (already fixed?)")

# ── 3. Fix 7_Backtesting.py import ───────────────────────────────────────────
bt_path = "pages/7_Backtesting.py"
src = open(bt_path, encoding="utf-8").read()
old = "from quantlib_pro.data.providers import DataProviderFactory"
new = "from quantlib_pro.data.providers_legacy import DataProviderFactory"
if old in src:
    open(bt_path, "w", encoding="utf-8").write(src.replace(old, new))
    print(f"[3] Fixed DataProviderFactory import in {bt_path}")
else:
    print(f"[3] Pattern not found in {bt_path} (already fixed?)")

print("\nDone.")
