# Dictate for macOS

**Community port by [Diane Green](https://github.com/dianegreendesign).** Originally contributed through [member repository PR #1](https://github.com/SRC-Rabbit-Hole/dictate-starter/pull/1), merged August 3, 2026. That repository may require member access. [Public authorship record](../AUTHORS.md).

Hold **Right Command + Right Option**, wait for the cue, speak and release either key. Audio goes to Groq Whisper (or OpenAI if configured). The result is pasted at the cursor and saved in `dictation-log.md`. This port runs headless, with sound and notifications rather than a menu-bar icon.

This public edition retains the contributed implementation with targeted maintenance documented in the [changelog](../CHANGELOG.md). Windows behavior must not be assumed here: macOS insertion uses the clipboard and restores **text only**, not images/files. It does not guard against switching destination apps while a network request is running. Keep the destination focused and release both keys before the result arrives. Review the text before sending.

## Install

Use **macOS 14 or later and Python 3.12**. The locked dependency wheels target macOS; Apple Silicon is the CI target. Intel hardware and current OS permissions need separate acceptance. Keep the project outside protected Documents/Desktop/Downloads folders if the app cannot read its files.

Download and extract [Dictate-0.1.0-source.zip](https://github.com/dianewhiddon/dictate-desktop/releases/tag/v0.1.0), then open Terminal in its `macos` folder:

```bash
bash install-macos.sh
```

If your Python executable has another name, use `PYTHON=/path/to/python3.12 bash install-macos.sh`. Setup creates a virtual environment, installs the hashed lock, checks packages, and builds an **unsigned local** `Dictate.app`. It does not launch it, change permissions, or add Login Items.

1. Add `GROQ_API_KEY` to the generated `.env` using [Groq Console](https://console.groq.com/). OpenAI is an alternate transcription provider.
2. Launch `Start Dictate.command` for the first console test. On macOS, Accessibility, Input Monitoring and Microphone permissions may be needed for the actual Python/Terminal or app launch route. Follow the operating system's prompts; permission attribution varies with that route. Restart after granting access.
3. Test a short phrase in a disposable text document. Check `dictation-log.md` as well as the inserted result.

Double-click `Dictate.app` for a background launch. Adding it to System Settings → General → Login Items is optional and manual. The original contributor reported menu-bar toolkit problems on macOS 26; the headless implementation is intentional.

## Settings and controls

Put overrides in `config.local.toml`, then run `Restart Dictate.command`. Default keys, audio device, provider/model, volume, snippets path, history and paste combination are in `config.toml`. Two distinct supported keys are required. Paste combinations are `cmd+v` and `cmd+shift+v`.

Cleanup is **off by default**. To opt in:

```toml
[cleanup]
enabled = true
```

Groq then receives the transcript and full snippet table as well as the recorded audio. Its cleanup model is configured separately from transcription. OpenAI cleanup is also supported. Incomplete cleanup responses fall back to the raw transcript with local snippets. AI cleanup is probabilistic and can change wording.

- **Start Dictate.command:** console launch.
- **Quit Dictate.command:** verifies this installation's recorded PID and exact command, requests shutdown, and waits for active work to save. It never searches for processes by a shared filename.
- **Restart Dictate.command:** completes that shutdown before opening this installation's app bundle.

The new sound module uses local `afplay` cues. History is saved before paste. Failed transcription or capture preserves audio in `recordings/`. Clipboard restoration will not overwrite a newer text value copied by the user during insertion. Rich clipboard formats remain unsupported.

## Update or remove

Quit first and keep a backup of `.env`, `config.local.toml`, personal snippets and history. Extract an update to a new permanent location, run its installer, and copy your local files deliberately. Remove the old Login Item and add the new app only after testing. Do not run both copies.

To uninstall, quit this installation, remove its optional Login Item, and delete its folder. Delete custom history/snippets, saved recordings and backups separately if wanted. API keys in other applications are unaffected.

## Troubleshooting and limits

Read `dictate.log` (rotating diagnostics) and `dictate-launch.log` (launcher output). Do not upload keys, actual transcripts or recordings. A missing PortAudio library requires installation of that library for your Python environment; microphone access must still be tested locally.

Automated software checks cover recovery, provider response handling, clipboard ownership, settings and scoped process control. They do **not** prove real microphone capture, permissions, app-bundle launch or reliable paste into arbitrary applications. No signed/notarized binary is provided. [Shared privacy guidance](../docs/privacy.md) and the [MIT license](../LICENSE) apply.
