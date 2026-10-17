# Dictate

**Hold two keys, speak, release. Your words appear in your Windows app.**

A small Python tray utility with recoverable transcripts, voice snippets and optional AI cleanup. Windows typing leaves the clipboard alone. Created by [Diane Whiddon](https://github.com/dianewhiddon); MIT licensed.

The separate **[macOS port](macos/README.md) is by [Diane Green](https://github.com/dianegreendesign)**. Her headless implementation and credit are preserved. See [authors and contribution history](AUTHORS.md).

![Recent dictations with fictional sample text](docs/images/recents.png)

## Download and install on Windows

Requires **Windows 10/11 x64, 64-bit Python 3.12, internet access and your own Groq or OpenAI API key**. Optional cleanup uses an Anthropic API key. Provider charges and limits apply.

1. Download **Dictate-0.1.1-source.zip** from [Releases](https://github.com/dianewhiddon/dictate-desktop/releases/tag/v0.1.1). Extract it to a permanent folder you control.
2. Install [Python 3.12](https://www.python.org/downloads/windows/) with its `py` launcher if needed.
3. Open PowerShell in the extracted folder:

```powershell
.\install.ps1
notepad .env
```

Add `GROQ_API_KEY` from [Groq Console](https://console.groq.com/). To use OpenAI instead, follow [configuration](docs/configuration.md). Cleanup is off by default; it requires both an explicit setting and an Anthropic key.

If Windows blocks the downloaded script, inspect it, then run `Unblock-File .\install.ps1` and retry. A computer's execution policy can still restrict scripts. You can also follow the equivalent environment and locked-install commands in `install.ps1`. Pass `-Python 'C:\path\to\python.exe'` if the launcher is unavailable.

The installer creates `.venv`, verifies the Python version, installs version- and hash-locked dependencies, and creates local configuration templates. It does not launch Dictate, request administrator access, or enable startup. This is a **source distribution with a setup script**, not a signed standalone executable. Git is optional.

## First use

Quit any other Dictate installation. The single-instance guard prevents duplicate recording and insertion.

```powershell
.\.venv\Scripts\python.exe dictate.py
```

1. Put the cursor in a text editor.
2. Hold **Left Ctrl + Left Windows**. Wait for the start sound before speaking.
3. Speak a short sentence, then release either key and let both keys up.
4. Keep that window focused until the text arrives. Review it before sending.

The tray icon is **gray when idle, gold while recording, light gold while processing**. Its tooltip also names the state. Left-click for **Recent dictations**. Click a row or press its number to copy the complete transcript. Press **L** to open the full log; **Esc** closes the popup. Opening or dismissing it does not copy anything.

For later launches, double-click `start-dictate.vbs`. Optional Desktop and login-startup shortcuts:

```powershell
.\setup-startup.ps1
```

Shortcuts are named **Dictate Desktop**. The script refuses to replace another installation's shortcut and validates all destinations before changing any. To create only a shortcut in a chosen existing folder, pass `-Directory 'C:\your\folder'`. Setup alone never enables startup.

## Recovery and privacy

Transcripts are saved before insertion by default. Changing windows, held modifiers, an open menu or a rejected input stops insertion; recover the text from Recents. Focus guards follow the window, not individual fields inside it. Some text can already have been inserted when focus changes.

Transcription failures retain a WAV under `recordings/`. Dropped or excessive audio is saved for review instead of being silently transcribed as a complete recording. The microphone closes when recording ends. A ten-minute limit prevents unbounded capture; it is not a promise about practical provider limits or processing speed.

Audio goes to **Groq**, or **OpenAI** if selected. Optional cleanup sends the transcript and full snippet table to **Anthropic**. AI cleanup can still alter wording; leave it off when you want the raw transcript plus exact local snippet matching. Dictate has no telemetry and never presses Send. [Data storage, privacy and costs](docs/privacy.md).

## Configure, update or remove

Use **Open config** to edit `config.local.toml`, then **Reload config** while idle. Keep personal snippets in a separate `*.local.md` file so updates do not overwrite them. [All settings and examples](docs/configuration.md).

For a ZIP update, quit Dictate, remove its old shortcuts with `setup-startup.ps1 -Remove`, extract the new release into a new folder and run its installer. Copy your own `.env`, `config.local.toml`, personal snippets and any history you want to retain. Recreate optional shortcuts only after a successful test. Keep the old folder until verified.

For a Git checkout, quit, back up your local files, then `git pull --ff-only` and run `install.ps1`. Never overwrite divergent work to force an update.

To uninstall, quit and run `setup-startup.ps1 -Remove` from that installation (use the same `-Directory` if you chose one). Delete its folder. History, failed recordings, custom files outside it, backups and clipboard history require separate deletion. Do not delete files shared with another application.

## macOS

The [community port](macos/README.md) keeps Diane Green's Right Command + Right Option workflow, Groq cleanup option and local `.app` launcher. It uses clipboard paste and restores **text only**; copied images/files are not preserved. It has separate code and dependency locks. Automated checks do not establish microphone, permissions, clipboard or app-bundle behavior on a person's Mac. Read its instructions and limitations before installing.

## Development

[Architecture and contribution guide](CONTRIBUTING.md) · [Design system](DESIGN.md) · [Security](SECURITY.md) · [Verification and limits](docs/verification.md) · [Troubleshooting](docs/troubleshooting.md) · [Changelog](CHANGELOG.md)

Each release includes an exact-commit source ZIP and SHA-256 checksums. Windows and macOS software checks run through GitHub Actions. Hardware acceptance is recorded separately. Contributions should include focused regression tests and preserve platform-specific behavior and authorship.
