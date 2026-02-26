"""Restore pages 9-14 from emoji-named versions in git commit 3fbe1db."""
import subprocess, os, re, ast, collections

# emoji git path -> (clean target name, material icon)
mapping = {
    "pages/9_\U0001f4da_Data_Management.py":       ("pages/9_Data_Management.py",      "database"),
    "pages/10_\U0001f4c8_Market_Analysis.py":       ("pages/10_Market_Analysis.py",     "show_chart"),
    "pages/11_\U0001f4e1_Trading_Signals.py":       ("pages/11_Trading_Signals.py",     "radar"),
    "pages/12_\U0001f30a_Liquidity.py":             ("pages/12_Liquidity.py",           "water"),
    "pages/13_\U0001f578\ufe0f_Systemic_Risk.py":   ("pages/13_Systemic_Risk.py",       "hub"),
    "pages/14_\U0001f9e0_Trader_Stress_Monitor.py": ("pages/14_Trader_Stress_Monitor.py","psychology"),
}

EMOJI_RE = re.compile(
    "[\U00010000-\U0010ffff\u2600-\u27bf\ufe00-\ufe0f\u2300-\u23ff\u2b00-\u2bff\U0001f000-\U0001f9ff]+",
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

# First, list all files in commit 3fbe1db pages/ to find exact paths
ls = subprocess.check_output(["git", "ls-tree", "--name-only", "3fbe1db", "pages/"])
available = ls.decode("utf-8").splitlines()
print("Available in 3fbe1db:", [p for p in available if any(x in p for x in ['9_','10_','11_','12_','13_','14_'])])

restored = []
for git_path, (target, icon) in mapping.items():
    # Find the actual path from git ls-tree output
    match = None
    for avail in available:
        if avail.encode("utf-8") == git_path.encode("utf-8"):
            match = avail
            break
    if not match:
        # Try byte-level match
        for avail in available:
            if git_path.encode() in avail.encode():
                match = avail
                break
    if not match:
        print(f"NOT FOUND in git: {git_path!r}")
        continue

    try:
        blob = subprocess.check_output(
            ["git", "show", f"3fbe1db:{match}"],
            stderr=subprocess.DEVNULL,
        )
        src = blob.decode("utf-8")

        # Check indentation quality
        lines = src.splitlines()
        indents = collections.Counter(
            len(l) - len(l.lstrip()) for l in lines if l.strip() and l[0] == ' '
        )
        min_indent = min(indents.keys()) if indents else 4
        print(f"  {os.path.basename(match)}: min_indent={min_indent}, dist={sorted(indents.items())[:5]}")

        src = patch_icons(src, icon)
        ast.parse(src)  # verify syntax
        with open(target, "w", encoding="utf-8") as f:
            f.write(src)
        restored.append(os.path.basename(target))
    except subprocess.CalledProcessError as e:
        print(f"GIT FAILED  {match}: {e}")
    except SyntaxError as e:
        print(f"SYNTAX BAD  {target}: line {e.lineno} — {e.msg}")
    except Exception as e:
        print(f"ERROR: {e}")

print(f"\nRestored {len(restored)}: {', '.join(restored)}")
