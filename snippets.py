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
    replacements = {phrase.casefold(): expansion for phrase, expansion in snippets if phrase}
    if not replacements:
        return text
    phrases = sorted(replacements, key=len, reverse=True)
    pattern = r"(?<!\w)(?:" + "|".join(map(re.escape, phrases)) + r")(?!\w)"
    # One pass: expansion contents never trigger another snippet.
    return re.sub(
        pattern, lambda match: replacements[match.group().casefold()], text, flags=re.IGNORECASE
    )
