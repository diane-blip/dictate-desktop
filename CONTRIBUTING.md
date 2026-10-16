# Contributing

Keep Dictate small, understandable and dependable at the moment someone finishes speaking. Explain the problem and the observable behavior before proposing an abstraction or dependency.

## Local checks

Use Windows and Python 3.12. Install the locked runtime with `install.ps1`, then development tools:

```powershell
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-dev.txt
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe -m unittest discover -v
```

The default suite is offline and does not record audio or write to the clipboard. Window/input integration tests are opt-in, open a temporary editor and require an interactive Windows session:

```powershell
$env:DICTATE_INTEGRATION = "1"
.\.venv\Scripts\python.exe -m unittest test_insert test_process test_recents -v
Remove-Item Env:DICTATE_INTEGRATION
```

Do not use real client text or keys in fixtures. Keep tests about failures and contracts, not private implementation details.

## Architecture

`dictate.py` owns the idle → recording → processing → idle lifecycle. Tk owns the main thread and popup. One polling thread owns microphone start/stop. A single processing worker handles each completed recording; another recording cannot begin while it is busy. Configuration reload and Quit refuse to interrupt active work.

| Module | Responsibility |
|---|---|
| `hotkeys.py` | Poll two Win32 key states every 20ms; no global hook or suppressed keys |
| `audio.py` | Refresh device enumeration, retry inputs until frames arrive, produce mono PCM WAV |
| `transcribe.py` | Fixed provider endpoints, finite network timeouts, validated responses |
| `cleanup.py` | Optional bounded cleanup, reject incomplete/commentary/POV-changing responses, fall back |
| `insert.py` | UTF-16 input batches, modifier-release and foreground-window checks, no clipboard fallback |
| `log.py` | Append-only multiline recovery and bounded history reads |
| `recents.py` | Explicit selection of saved text; only its copy action writes the clipboard |
| `settings.py` | Shipped defaults, validated local overrides, reloadable provider keys |

The loopback socket on port 49731 enforces one local instance, including the original personal edition. It accepts no commands. Port collision is reported as another instance; this is not a network service.

PortAudio is rebuilt between recordings because an openable endpoint can still deliver no frames after a device change. This uses sounddevice's private initialization functions. The dependency is pinned, with mocked recovery tests and a real-device acceptance check for dependency upgrades. Keep that tradeoff explicit.

## Changes that need regression coverage

Clipboard preservation; explicit copy; recovery before insertion; stale destination; Unicode and emoji; provider timeout/malformed/truncated responses; config changes during work; device failover; startup/quit. Preserve the contributor's macOS history and label platform-specific claims.

## Dependencies

`requirements.txt` lists direct dependency ranges. `requirements.lock` is the tested Windows/Python 3.12 resolution with hashes. Regenerate deliberately on that platform:

```powershell
.\.venv\Scripts\uv.exe pip compile requirements.txt --generate-hashes --python-version 3.12 --python-platform x86_64-pc-windows-msvc --no-header -o requirements.lock
.\.venv\Scripts\python.exe -m pip_audit -r requirements.lock --disable-pip --no-deps
```

Test installation into a fresh environment after lock changes. Do not hand-edit hashes or silence audit findings without a recorded reason. See [release checks](docs/releasing.md).

Small fixes can be pull requests. For larger changes, describe the user need and maintenance cost first. There is no promised support response time.

## Hosted checks

The active [GitHub workflow](.github/workflows/checks.yml) runs Windows and macOS software checks with read-only permissions and commit-pinned actions. Native Windows interaction checks and real hardware acceptance are separate.

## Public edition and macOS contributions

Read AUTHORS.md before describing provenance. Keep `macos/` independent; preserve its contributor credit and verify platform-specific changes on macOS. Platform-neutral copies (`audio.py`, `log.py`, `snippets.py`, `transcribe.py`) must be compared when porting fixes. Do not silently import the Windows keyboard or sound backend into macOS.

The five controlled Windows interaction checks require `DICTATE_INTEGRATION=1` and an interactive desktop. Keep hands off the temporary test editor. Never run dictation-key injection beside a real installation using that pair.

macOS checks: from `macos/`, set `PYNPUT_BACKEND=dummy` and run `python -m unittest discover -s . -p "test_*.py"`. The dummy backend is for tests only; never set it for ordinary use. Real hardware, OS permissions and app-bundle acceptance remain separate.

Generate the macOS lock with the pinned uv compiler using the command above with `macos/requirements.txt`, `--python-platform aarch64-apple-darwin` and output `macos/requirements.lock`. Development: `uv pip compile requirements-dev.in --universal --generate-hashes --no-header -o requirements-dev.txt`. Inspect every version/provenance change, test it and audit the new locks.
