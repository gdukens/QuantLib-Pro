import subprocess, os, re, ast

raw_mapping = {
    b"pages/9_\xf0\x9f\x93\x9a_Data_Management.py": ("pages/9_Data_Management.py", "database"),
    b"pages/10_\xf0\x9f\x93\x88_Market_Analysis.py": ("pages/10_Market_Analysis.py", "show_chart"),
    b"pages/11_\xf0\x9f\x93\xa1_Trading_Signals.py": ("pages/11_Trading_Signals.py", "radar"),
    b"pages/12_\xf0\x9f\x8c\x8a_Liquidity.py": ("pages/12_Liquidity.py", "water"),
    b"pages/13_\xf0\x9f\x95\xb8\xef\xb8\x8f_Systemic_Risk.py": ("pages/13_Systemic_Risk.py", "hub"),
    b"pages/14_\xf0\x9f\xa7\xa0_Trader_Stress_Monitor.py": ("pages/14_Trader_Stress_Monitor.py", "psychology"),
}
EMOJI_RE = re.compile(
    u"[\U00010000-\U0010ffff\u2600-\u27bf\ufe00-\ufe0f\u2300-\u23ff\U0001f000-\U0001f9ff]+",
    re.UNICODE,
)
ST_RE = re.compile(
    r"""(st\.(title|header|subheader|sidebar\.header|sidebar\.subheader)\s*\(\s*)(['"])(.+?)\3""",
    re.DOTALL,
)

def clean(src, icon):
    def repl(m):
        label = EMOJI_RE.sub("", m.group(4)).strip()
        q = m.group(3)
        return f"{m.group(1)}{q}{label}{q}, icon={q}:material/{icon}:{q}"
    out = ST_RE.sub(repl, src)
    return EMOJI_RE.sub("", out)

restored = []
ls_out = subprocess.check_output(["git", "ls-tree", "-r", "--long", "3fbe1db"])
for raw_path, (target, icon) in raw_mapping.items():
    git_ref = b"3fbe1db:" + raw_path
    try:
        blob = subprocess.check_output(["git", "cat-file", "blob", git_ref], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        # fallback: match by blob hash from ls-tree
        suffix_bytes = raw_path.split(b"/")[-1]
        found_hash = None
        for line in ls_out.splitlines():
            if suffix_bytes in line:
                found_hash = line.split()[2]
                break
        if not found_hash:
            print(f"NOT FOUND: {raw_path}")
            continue
        blob = subprocess.check_output(["git", "cat-file", "blob", found_hash])
    src = blob.decode("utf-8")
    src = clean(src, icon)
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"SYNTAX BAD {target}: L{e.lineno} {e.msg}")
        continue
    with open(target, "w", encoding="utf-8") as f:
        f.write(src)
    restored.append(os.path.basename(target))
    print(f"OK: {target}")

print(f"Done: {restored}")
