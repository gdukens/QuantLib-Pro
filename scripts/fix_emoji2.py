"""
Fix label text in Streamlit pages:
1. st.title/header/subheader: the label already has :material/xxx: prefix text — remove it
2. All other string contexts (tabs, expander, metric, button, markdown): same cleanup
The icon="" parameters on headings are already correct — leave them alone.
"""
import os
import re

# Matches :material/icon_name: or :material/icon_name: followed by optional space
# Used to strip the shortcode from label text
MATERIAL_SHORTCODE_RE = re.compile(r":material/[a-zA-Z_/]+:\s*")

# Matches the icon= kwarg (already correct — keep it)
# ICON_KWARG_RE = re.compile(r',\s*icon\s*=\s*"[^"]*"')   # don't touch

# st.title/header/subheader first argument — strip :material/...: from label only
# Pattern captures function call up to first closing quote of first arg
HEADING_LABEL_RE = re.compile(
    r"""(st\.(?:title|header|subheader)\s*\(\s*f?)(['"])(.*?)(\2)""",
    re.DOTALL,
)


def fix_heading_label(m: re.Match) -> str:
    prefix = m.group(1)   # st.title( or st.header(f  etc
    q = m.group(2)        # quote char
    label = m.group(3)    # string content
    # group(4) is the closing quote

    clean = MATERIAL_SHORTCODE_RE.sub("", label).strip()
    return f"{prefix}{q}{clean}{q}"


def process_file(path: str) -> bool:
    with open(path, encoding="utf-8") as f:
        src = f.read()
    original = src

    # Fix heading labels — remove :material/...: prefix from the label text
    src = HEADING_LABEL_RE.sub(fix_heading_label, src)

    # Fix all other occurrences of :material/xxx: that leaked into regular strings
    # (tab labels, expander titles, metric labels, markdown, captions, buttons)
    # BUT: preserve icon= kwarg values — only strip when NOT inside icon="..."
    # Simple approach: strip shortcodes that are NOT preceded by icon=
    # We use a negative lookbehind for icon=
    src = re.sub(
        r'(?<!icon="):material/[a-zA-Z_/]+:\s*',
        "",
        src,
    )

    # Clean up double spaces created by stripping
    src = re.sub(r"  +", " ", src)
    # Remove trailing space before a closing quote in simple string arguments
    src = re.sub(r" +(\"|\')(\s*(?:,|\)))", r"\1\2", src)

    if src != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
        return True
    return False


if __name__ == "__main__":
    pages_dir = os.path.join(os.path.dirname(__file__), "..", "pages")
    changed = []
    for fname in sorted(os.listdir(pages_dir)):
        if not fname.endswith(".py"):
            continue
        path = os.path.join(pages_dir, fname)
        if process_file(path):
            changed.append(fname)

    print("Fixed files:")
    for f in changed:
        print(f"  {f}")
    print(f"Total: {len(changed)} files cleaned.")
