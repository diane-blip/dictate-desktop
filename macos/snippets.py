"""Voice snippets: say a phrase, get its expansion inserted.

The snippet file is a Markdown table:

    | Say            | Insert    |
    |----------------|-----------|
    | brand pink     | #F49CBB   |
"""
import re
from pathlib import Path


def load_snippets(path: Path) -> list[tuple[str, str]]:
    if not path.exists():
        return []
    snippets = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2 or not cells[0] or not cells[1]:
            continue
        if set(cells[0]) <= {"-", " ", ":"}:  # header separator row
            continue
        if cells[0].lower() in ("say", "phrase", "trigger"):  # header row
            continue
        snippets.append((cells[0], cells[1]))
    return snippets


def apply_local(text: str, snippets: list[tuple[str, str]]) -> str:
    """Fallback matching when the AI cleanup pass is unavailable: exact
    phrase replacement, case-insensitive, longest phrases first."""
    for phrase, expansion in sorted(snippets, key=lambda s: -len(s[0])):
        pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
        text = re.sub(pattern, expansion.replace("\\", "\\\\"), text, flags=re.IGNORECASE)
    return text
