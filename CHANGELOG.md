# Changelog

## 0.1.0 · October 15, 2026

First personal-profile public source release, based on the previously prepared member edition.

- Neutral gray, white, teal and blue Windows tray/Recents styling; larger readable text, keyboard log action and generated microphone icon.
- Cloud cleanup off by default, bounded output budget and HTTP-client cleanup even when SDK construction fails.
- Bounded audio capture; dropped, overlong or interrupted captures retain their WAV instead of appearing complete. Destination menus block Windows insertion.
- Hash-locked runtime and development dependencies; Windows/macOS automated checks and documented release verification.
- Diane Green's macOS port preserved and credited. Added its missing sound module; history now precedes paste; incomplete cleanup falls back; modifier/clipboard failure cleanup is guarded; Quit/Restart target only this installation and wait for work to save; installer/bundle avoid broad process kills and recursive bundle deletion. Removed unused macOS GUI dependencies.
- Separate public repository and shortcut names; no personal installation data, API keys, recordings or private history included.

## Earlier member-edition history

## Unreleased

Windows public-release candidate, pending owner approval.

- Port clipboard-free Unicode insertion and explicit Recents copying from the daily-use application.
- Capture the foreground destination before recording; retain text before insertion.
- Replace the global keyboard library with native held-key polling.
- Keep configuration reload and Quit from interrupting active work.
- Validate local configuration overrides without overwriting shipped defaults.
- Bound history reads and preserve multiline entries; rotate diagnostic logs.
- Reject incomplete cleanup responses, close API clients, and omit provider bodies from transcription errors.
- Use single-pass literal snippet replacement.
- Add regression tests, hashed Windows dependencies and release/development documentation.
- Use explicit system-certificate TLS contexts instead of a global certificate monkeypatch.
- Preserve the credited macOS implementation as a separate community port.

### Migrating an existing Windows starter

Quit the old app first. Back up your own configuration, snippets, keys and history privately.
Reconcile customized `config.toml` with the new defaults and move overrides into `config.local.toml`.
Remove `paste_combo` and `restore_clipboard` from Windows settings: normal insertion no longer uses either.
Keep personal snippets outside tracked `snippets.md` and point to them from your local configuration.
Run the installer to update dependencies, then test in a text editor.

Existing Markdown history is readable; multiline entries written by older versions may already have lost their boundaries. Nothing reconstructs missing text. Your installed personal edition is a separate repository and does not update from this starter.
