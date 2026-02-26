"""
Replace emoji in all Streamlit page files with Material Design icons.
- st.title/header/subheader: strip emoji from label, add icon="..." parameter
- All other contexts (tabs, expander, metric, caption, markdown): just strip emoji
"""
import os
import re

# Map of emoji → Material Design icon name
ICON_MAP = {
    "📈": ":material/trending_up:",
    "📉": ":material/trending_down:",
    "📊": ":material/bar_chart:",
    "📡": ":material/radar:",
    "🌊": ":material/waves:",
    "🕸️": ":material/hub:",
    "🕸": ":material/hub:",
    "🧠": ":material/psychology:",
    "⚠️": ":material/warning:",
    "⚠": ":material/warning:",
    "🎯": ":material/my_location:",
    "📚": ":material/library_books:",
    "🧪": ":material/science:",
    "📶": ":material/signal_cellular_alt:",
    "🎬": ":material/movie:",
    "🌐": ":material/public:",
    "💹": ":material/candlestick_chart:",
    "⚙️": ":material/settings:",
    "⚙": ":material/settings:",
    "🔥": ":material/local_fire_department:",
    "🛡️": ":material/shield:",
    "🛡": ":material/shield:",
    "💡": ":material/lightbulb:",
    "🏆": ":material/emoji_events:",
    "🥧": ":material/pie_chart:",
    "🎓": ":material/school:",
    "😀": ":material/show_chart:",
    "🎮": ":material/tune:",
    "⚔️": ":material/sports_score:",
    "⚔": ":material/sports_score:",
    "🔍": ":material/search:",
    "📥": ":material/download:",
    "💾": ":material/save:",
    "🚀": ":material/rocket_launch:",
    "⚡": ":material/bolt:",
    "💿": ":material/storage:",
    "📁": ":material/folder_open:",
    "🔄": ":material/sync:",
    "📋": ":material/assignment:",
    "🔗": ":material/link:",
    "📅": ":material/calendar_today:",
    "📓": ":material/note_alt:",
    "📹": ":material/videocam:",
    "📖": ":material/menu_book:",
    "🧘": ":material/self_improvement:",
    "✅": "",
    "❌": "",
    "🔴": "",
    "🔵": "",
    "🟢": "",
    "🟡": "",
    "📑": ":material/table_chart:",
    "🎲": ":material/casino:",
    "🧮": ":material/calculate:",
    "🔮": ":material/auto_awesome:",
    "📜": ":material/description:",
    "🛠️": ":material/build:",
    "🛠": ":material/build:",
    "📌": ":material/push_pin:",
    "⭐": "",
    "💰": ":material/payments:",
    "💵": ":material/attach_money:",
    "🏦": ":material/account_balance:",
    "📝": ":material/edit_note:",
    "🔒": ":material/lock:",
    "🔓": ":material/lock_open:",
    "⏱️": ":material/timer:",
    "⏱": ":material/timer:",
    "📐": ":material/straighten:",
    "🧩": ":material/extension:",
    "💼": ":material/business_center:",
}

# Sorted longest-first so multi-char emoji match before single-char base
SORTED_EMOJI = sorted(ICON_MAP.keys(), key=len, reverse=True)
EMOJI_RE = re.compile("|".join(re.escape(e) for e in SORTED_EMOJI))

# Match st.title/header/subheader with a plain or f-string first argument
HEADING_RE = re.compile(
    r"""(st\.(?:title|header|subheader))\s*\(\s*(f?)(['"])(.*?)(\3)""",
    re.DOTALL,
)


def first_icon(text: str) -> str:
    for e in SORTED_EMOJI:
        if e in text and ICON_MAP[e]:
            return ICON_MAP[e]
    return ""


def strip_emoji_text(text: str) -> str:
    """Remove emoji entirely from heading label text (icon goes in icon= param)."""
    result = EMOJI_RE.sub("", text)
    result = BROAD_EMOJI_RE.sub("", result)
    return result.strip()


def replace_heading(m: re.Match) -> str:
    fn = m.group(1)        # st.title / st.header / st.subheader
    fprefix = m.group(2)   # "f" or ""
    q = m.group(3)         # quote character
    label = m.group(4)     # string content
    # group(5) is the closing quote — consumed

    icon = first_icon(label)
    clean = strip_emoji_text(label)

    if icon:
        return f'{fn}({fprefix}{q}{clean}{q}, icon="{icon}"'
    else:
        return f'{fn}({fprefix}{q}{clean}{q}'


# Strip misplaced :material/xxx: shortcodes from inside heading label strings
MATERIAL_TEXT_RE = re.compile(r":material/[a-z_]+:\s*")


def process_file(path: str) -> bool:
    with open(path, encoding="utf-8") as f:
        src = f.read()

    original = src

    # Step 0: undo prior bad run — remove icon= kwargs & material text from labels
    # Remove existing icon="..." kwargs that were already injected
    src = re.sub(r',\s*icon\s*=\s*"[^"]*"', "", src)
    # Remove :material/xxx: text that leaked into heading label strings
    src = MATERIAL_TEXT_RE.sub("", src)

    # Step 1: fix st.title/header/subheader labels + inject icon=
    src = HEADING_RE.sub(replace_heading, src)

    # Step 2: strip any remaining emoji (known map first, then broad sweep)
    src = EMOJI_RE.sub(lambda m: ICON_MAP.get(m.group(0), ""), src)
    src = BROAD_EMOJI_RE.sub("", src)

    # Step 3: clean up artefacts — only collapse multiple consecutive spaces
    src = re.sub(r"  +", " ", src)

    if src != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
        return True
    return False


# Broad regex that catches ANY emoji/symbol not already in ICON_MAP
ALL_EMOJI_RE = re.compile(
    "["
    "\U0001F000-\U0001FFFF"   # most emoji blocks
    "\U00002600-\U000027BF"   # misc symbols
    "\U0000FE00-\U0000FE0F"   # variation selectors
    "\U00002702-\U000027B0"
    "\U0000200D"              # ZWJ
    "\U0000FE0F"              # VS-16
    "\U00000023-\U00000039"   # ASCII range — skip
    "]+",
    flags=re.UNICODE,
)
# Simpler catch-all: anything outside BMP that looks like emoji
BROAD_EMOJI_RE = re.compile(
    r"[\U0001F300-\U0001FFFF\U00002600-\U000027BF\U0001FA00-\U0001FA99"
    r"\U00002702-\U000027B0\uFE00-\uFE0F\u200D]+"
)


def strip_all_emoji(src: str) -> str:
    """Strip all emoji that remain after ICON_MAP substitution."""
    return BROAD_EMOJI_RE.sub("", src)


if __name__ == "__main__":
    pages_dir = os.path.join(os.path.dirname(__file__), "..", "pages")
    changed = []
    for fname in sorted(os.listdir(pages_dir)):
        if not fname.endswith(".py"):
            continue
        path = os.path.join(pages_dir, fname)
        if process_file(path):
            changed.append(fname)

    print("Changed files:")
    for f in changed:
        print(f"  {f}")
    print(f"Total: {len(changed)} files modified.")
