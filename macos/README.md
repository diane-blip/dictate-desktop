# Dictate — macOS port

**Community port by [dianegreendesign](https://github.com/dianegreendesign), contributed in [PR #1](https://github.com/SRC-Rabbit-Hole/dictate-starter/pull/1).** This implementation is preserved separately from the October 2026 Windows refresh. Its runtime has not been revalidated on macOS for that release. The clipboard path restores text only; copied images and files are not preserved. API charges and limits apply. The Windows release's focus, cleanup and lifecycle improvements do not automatically apply here.

Hold-to-talk dictation you own outright. Hold two keys anywhere, speak, release,
and the transcribed text appears at your cursor, cleaned up, with your personal
shorthand expanded. Plain Python, using your own API key.

This is a macOS port of the root [Dictate Starter](../) (Windows). Same idea and
same cleanup logic; the OS-integration layer is rewritten for macOS, and it runs
**headless** (see "No menu bar" below).

## What it does

- Hold **Right Command + Right Option** together and speak.
- Release either key. Your audio goes to **Groq Whisper** for transcription
  (fast, free-tier friendly).
- A **Groq Llama cleanup pass** strips ums and false starts, resolves
  self-corrections, and applies your snippets (say "my email", get your address).
  It's hard-banned from changing your pronouns; on any failure or timeout you get
  the raw transcript, so dictation never hangs on the LLM.
- The text is pasted at your cursor, and your previous clipboard is restored.
- A soft boop marks start and stop. The start cue plays only after Dictate proves audio is flowing. Each hold rebuilds the system audio session, resolves the devices again, and automatically tries another input when an endpoint is dead. Everything is appended to `dictation-log.md`
  (gitignored). Recordings auto-stop at 10 minutes and still transcribe in full.

Groq powers both transcription and cleanup with one `GROQ_API_KEY`. Check your current account limits and pricing. OpenAI is a config switch away.

## Setup

Requires **Python 3.11+** (`brew install python` if needed). From this folder:

```bash
bash install-macos.sh
```

That builds the environment and `Dictate.app`, then prints three one-time steps:

1. **Add your Groq key** to `.env` from [console.groq.com](https://console.groq.com).
2. **Grant permissions** (see below).
3. **Add `Dictate.app` to Login Items** so it starts on login.

### Permissions — the important part

macOS attributes permissions to the **Python** that runs the app, not to
"Dictate" or Terminal. In **System Settings > Privacy & Security**, grant these to
the Python at `./.venv/bin/python` (add it with the **+** button, using
Shift+Cmd+G to type the path):

- **Accessibility** — the global hotkey and the paste keystroke
- **Input Monitoring** — detecting the two held keys
- **Microphone** — prompted the first time you record

After granting, restart the app (Restart Dictate.command).

## No menu bar (why it's headless)

On recent macOS (tested on Tahoe / macOS 26), the system would not render a menu
bar status item for this app, not via pystray, not via rumps, not via a direct
AppKit status item, loose or bundled. So this port runs **headless**: the hotkey
pipeline with no menu bar. Feedback is the boops plus a notification; recent
dictations live in `dictation-log.md`.

Control it with the double-click commands (no menu needed):

- **Start Dictate.command** — start it in a Terminal window
- **Quit Dictate.command** — stop it
- **Restart Dictate.command** — after editing config
- `config.toml` — hotkey, sounds, volume, models
- `snippets.md` — your say → insert table (re-read live; no restart)

## Make it yours

- **Providers/models/hotkey:** `config.toml`.
- **Cleanup prompt:** `cleanup.py`.
- **Bundle identifier:** `make-app.sh` uses `com.example.dictate`; change it to
  your own.

## Optional: on-device transcription (Apple Silicon)

An M-series Mac can run Whisper locally (via MLX) for offline, zero-cost, fully
private transcription. Not included here; it would replace the transcription step.

## Troubleshooting

`dictate.log` and `dictate-launch.log` record startup and errors. Common ones:

- **Hotkey does nothing:** the permissions above aren't granted to
  `./.venv/bin/python`, or the app needs a restart after granting.
- **"Operation not permitted" on launch:** keep this project **out of your
  Documents/Desktop/Downloads folders**, which macOS protects; a launched app
  can't read its own files there.
- **Static instead of boops:** already handled here (sounds play via `afplay`, not
  through the mic's audio stream).

## Credit / license

Port of the Sway Rise Creative "Dictate Starter" (Windows). Same MIT license as
the root project (see [../LICENSE](../LICENSE)).
