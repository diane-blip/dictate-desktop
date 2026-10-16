"""Running log of everything dictated, appended to a markdown file."""
from datetime import datetime
from pathlib import Path

HEADER = """# Dictation log

Everything dictated through the Dictate app, newest at the bottom. Appended automatically after each insertion.
"""


def append_log(path: Path, text: str) -> None:
    text = text.strip()
    if not text:
        return
    now = datetime.now()
    day_heading = f"## {now:%Y-%m-%d}"

    if not path.exists():
        path.write_text(HEADER, encoding="utf-8")

    tail = path.read_text(encoding="utf-8")[-4000:]
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        if day_heading not in tail:
            f.write(f"\n{day_heading}\n\n")
        f.write(f"- **{now:%H:%M}** {text}\n")
