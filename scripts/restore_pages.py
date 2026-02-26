"""Restore core pages from the clean git commit 5b0afd4, strip emoji, add Material icons."""
import subprocess, os, re, ast

mapping = {
    "pages/1_\U0001f4c8_Portfolio.py":         ("pages/1_Portfolio.py",         "trending_up"),
    "pages/2_\u26a0\ufe0f_Risk.py":            ("pages/2_Risk.py",              "warning"),
    "pages/3_\U0001f4ca_Options.py":            ("pages/3_Options.py",           "bar_chart"),
    "pages/4_\U0001f3af_Market_Regime.py":      ("pages/4_Market_Regime.py",     "my_location"),
    "pages/5_\U0001f4c9_Macro.py":             ("pages/5_Macro.py",             "public"),
    "pages/6_\U0001f30a_Volatility_Surface.py": ("pages/6_Volatility_Surface.py","waves"),
    "pages/7_\U0001f4ca_Backtesting.py":        ("pages/7_Backtesting.py",       "replay"),
    "pages/8_\U0001f4ca_Advanced_Analytics.py": ("pages/8_Advanced_Analytics.py","analytics"),
    "pages/9_\U0001f9ea_Testing.py":            ("pages/15_Testing.py",          "science"),
    "pages/9_UAT_Dashboard.py":                 ("pages/16_UAT_Dashboard.py",    "fact_check"),
}

EMOJI_RE = re.compile(
    "[\U00010000-\U0010ffff"
    "\u2600-\u27bf"
    "\ufe00-\ufe0f"
    "\u2300-\u23ff"
    "\u2b00-\u2bff"
    "\U0001f000-\U0001f9ff"
    "]+",
    re.UNICODE,
)
ST_HEADING_RE = re.compile(
    r"""(st\.(title|header|subheader|sidebar\.header|sidebar\.subheader)\s*\(\s*)(['"])(.+?)\3""",
    re.DOTALL,
)

def strip_emoji(text):
    return EMOJI_RE.sub("", text).strip()

def patch_icons(src, icon_name):
    def repl(m):
        call  = m.group(1)
        quote = m.group(3)
        label = strip_emoji(m.group(4))
        return f'{call}{quote}{label}{quote}, icon={quote}:material/{icon_name}:{quote}'
    result = ST_HEADING_RE.sub(repl, src)
    result = EMOJI_RE.sub("", result)
    return result

restored = []
for git_path, (target, icon) in mapping.items():
    try:
        blob = subprocess.check_output(
            ["git", "show", f"5b0afd4:{git_path}"],
            stderr=subprocess.DEVNULL,
        )
        src = blob.decode("utf-8")
        src = patch_icons(src, icon)
        # Verify syntax
        ast.parse(src)
        with open(target, "w", encoding="utf-8") as f:
            f.write(src)
        restored.append(os.path.basename(target))
    except subprocess.CalledProcessError as e:
        print(f"GIT FAILED  {git_path}: {e}")
    except SyntaxError as e:
        print(f"SYNTAX BAD  {target}: {e}")
    except Exception as e:
        print(f"ERROR       {git_path}: {e}")

print(f"Restored {len(restored)} files: {', '.join(restored)}")
