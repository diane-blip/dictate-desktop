"""Append-only Markdown history; bounded reads independent of file size."""

import re
from collections import deque
from datetime import datetime
from pathlib import Path

HEADER = "# Dictation log\n\nPlaintext transcripts saved before insertion.\n"
_ENTRY = re.compile(r"^- \*\*\d\d:\d\d\*\* (.*)$")
_TAIL_BYTES = 256 * 1024


def _tail(path: Path, limit: int = _TAIL_BYTES) -> str:
    with path.open("rb") as stream:
        stream.seek(0, 2)
        size = stream.tell()
        stream.seek(max(0, size - limit))
        raw = stream.read(limit)
    if size > limit:
        raw = raw.partition(b"\n")[2]
    return raw.decode("utf-8", errors="replace")


def append_log(path: Path, text: str) -> None:
    if not text.strip():
        return
    heading = f"## {datetime.now():%Y-%m-%d}"
    path.parent.mkdir(parents=True, exist_ok=True)
    tail = _tail(path, 4096) if path.exists() else ""
    record = text.strip().replace("\n", "\n  ")
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        if not tail:
            stream.write(HEADER)
        if heading not in tail:
            stream.write(f"\n{heading}\n\n")
        stream.write(f"- **{datetime.now():%H:%M}** {record}\n")
        stream.flush()


def read_recent(path: Path, count: int = 10) -> list[str]:
    try:
        data = _tail(path)
    except FileNotFoundError:
        return []
    entries: deque[str] = deque(maxlen=count)
    for line in data.splitlines():
        match = _ENTRY.match(line)
        if match:
            entries.append(match.group(1))
        elif line.startswith("  ") and entries:
            entries[-1] += "\n" + line[2:]
    return list(entries)
