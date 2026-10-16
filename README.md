# Dictate

Hold two keys, speak, release. Dictate types the transcript into your Windows app while leaving your clipboard alone.

A small Python tray app with recoverable transcripts, configurable voice snippets and optional AI cleanup. Built by [Diane Whiddon](https://swayrisecreative.com/), used in her daily work, and shared under the [MIT license](LICENSE).

**Windows 10/11, Python 3.12, internet access and your own API key.** This is a source installation, not a signed standalone installer. Audio is transcribed by Groq or OpenAI. Optional cleanup sends the transcript and snippets to Anthropic. Provider usage limits and charges apply; see [privacy and costs](docs/privacy.md).

## Use it

1. Put the cursor where the text should go.
2. Hold **Left Ctrl + Left Windows** together. Wait for the start sound.
3. Speak, then release the keys. The tray icon turns gold while processing.
4. Keep the destination focused until the text arrives.

The icon is gray when idle and pink while recording. Left-click it to open **Recent dictations**; click a row to copy its complete text. Opening or closing Recents leaves the clipboard unchanged. Right-click for settings, snippets, history and Quit.

Transcripts are saved before insertion by default. A transcription failure saves the recording under `recordings/`. If the foreground window changes, insertion stops and the transcript remains in Recents. Review text before submitting it; Dictate never presses Send.

## Install on Windows

Install [Python 3.12](https://www.python.org/downloads/) with its **py launcher** and [Git](https://git-scm.com/downloads/win). Use a folder you control, outside a cloud-synced directory if you want local history to stay local.

In PowerShell:

```powershell
git clone https://github.com/SRC-Rabbit-Hole/dictate-starter.git
cd dictate-starter
.\install.ps1
notepad .env
```

Set `GROQ_API_KEY` from [Groq Console](https://console.groq.com/). An `ANTHROPIC_API_KEY` is optional. Without it, Dictate uses the raw transcript plus local snippet matching.

If Windows blocks the local setup script, inspect it, then run this one-process exception:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

Start in a console for your first test:

```powershell
.\.venv\Scripts\python.exe dictate.py
```

Speak a short sentence into a text editor. Check the transcript and Recents. After that, `start-dictate.vbs` launches without a console, or use the optional shortcuts:

```powershell
.\setup-startup.ps1
```

That creates Desktop and login-startup shortcuts. It refuses to overwrite a shortcut belonging to another installation. **Installation alone does not enable startup.** No administrator access is required.

## Customize, update or remove

Use **Open config** to edit untracked `config.local.toml`, then **Reload config** while idle. Your overrides survive updates. Edit `snippets.md` to map a spoken phrase to text, or point to your own file. See [configuration](docs/configuration.md).

For an update, quit Dictate, keep a private backup of your settings/snippets/history, then:

```powershell
git pull --ff-only
.\install.ps1
```

If Git reports local edits, preserve and reconcile them; do not reset your changes. Existing users should read [the migration notes](CHANGELOG.md) before updating.

To remove: quit, run `./setup-startup.ps1 -Remove` if you created shortcuts, then delete this installation folder when you no longer need its private history, recordings or keys. Copies in backups or synced folders remain.

## Limits and other platforms

- Windows insertion uses Unicode input events. Some applications reject them; elevated applications cannot receive input from a normal process. Recover the text from Recents instead of running Dictate as administrator.
- The focus guard tracks the foreground **window**, not every field inside it. Do not switch fields or type while insertion is in progress. Partial insertion is possible if focus changes mid-transcript.
- Network, transcription and cleanup can fail. Recovery helps, but neither recognition accuracy nor perfect word preservation is guaranteed.
- Recording auto-stops and processes at ten minutes. There is no offline transcription in this release.
- The [macOS port](macos/README.md), contributed by [dianegreendesign](https://github.com/dianegreendesign), is a separate community implementation. It uses clipboard paste, has different providers, and has not received this Windows release's acceptance testing. It cannot preserve image/file clipboard contents.

[Architecture and development](CONTRIBUTING.md) · [Privacy](docs/privacy.md) · [Troubleshooting](docs/troubleshooting.md) · [Security](SECURITY.md) · [Verification and limits](docs/verification.md) · [Release checklist](docs/releasing.md)
