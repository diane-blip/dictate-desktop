"""Stop only this installation's verified process; never match by filename."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
PID_FILE = APP_DIR / ".dictate.pid"


def owns_process(pid: int) -> bool:
    if pid <= 1:
        return False
    result = subprocess.run(
        ["/bin/ps", "-ww", "-p", str(pid), "-o", "command="],
        capture_output=True,
        text=True,
        check=False,
        timeout=3,
    )
    if result.returncode != 0:
        return False
    command = result.stdout.strip()
    suffix = f" {APP_DIR / 'dictate.py'}"
    if not command.endswith(suffix):
        return False
    interpreter = Path(command.removesuffix(suffix))
    # python.org framework builds re-exec their bundled Python.app binary.
    # Keep the script path exact; never accept a filename-only process match.
    allowed = {
        (APP_DIR / ".venv/bin/python").resolve(),
        (Path(sys.base_prefix) / "Resources/Python.app/Contents/MacOS/Python").resolve(),
    }
    return interpreter.resolve() in allowed


def stop() -> None:
    try:
        pid = int(PID_FILE.read_text(encoding="ascii").strip())
    except FileNotFoundError:
        print("This installation is not running.")
        return
    if not owns_process(pid):
        raise RuntimeError("Cannot verify the recorded process; no process was stopped.")
    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + 90
    while owns_process(pid):
        if time.monotonic() >= deadline:
            raise RuntimeError("Dictate is still saving work. Wait before restarting.")
        time.sleep(0.25)
    print("Dictate stopped after saving active work.")


if __name__ == "__main__":
    stop()
