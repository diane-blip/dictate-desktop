# Configuration

The root Windows app reads `config.toml`, then overlays `config.local.toml`. Edit the local file, not shipped defaults. Unknown local keys and invalid values fail before replacing the active configuration.

Example:

```toml
sound_volume = 0.15

[audio]
preferred_input = "USB microphone"

[cleanup]
enabled = false

[stt]
language = ""
```

Use the tray's **Reload config** while idle. Editing `.env` is also picked up on reload; an explicitly exported environment variable takes precedence. Missing transcription credentials produce a recoverable error, with the recording saved.

## Controls

Two distinct names from `left/right ctrl`, `left/right shift`, `left/right alt`, `left/right windows`, or `f1` through `f24`. For example, `"right ctrl"` and `"right alt"`. Left Ctrl with Alt is rejected because AltGr can synthesize that combination. Keys are observed, not intercepted; avoid combinations used by your other applications.

`min_hold_ms`: 0–2000. `max_seconds`: 1–600; reaching the cap stops and transcribes. `sound_volume`: 0–1. Turn `sounds` off to silence cues.

## Providers

Groq is the default transcription provider. For OpenAI, set `[stt] provider = "openai"` and supply `OPENAI_API_KEY`. Set the associated model field to an available transcription model. `language = ""` enables detection.

Cleanup defaults to Claude Haiku 5.5 with low reasoning effort. It is optional and falls back to the raw transcript with local snippets when unavailable. The timeout scales with text length up to 20 seconds. Custom model choices must support the request parameters in `cleanup.py`.

## Snippets and history

`snippets.md` is a two-column Markdown table. Local matching is case-insensitive, longest phrase first, in one pass. Expansions do not trigger further expansions. Embedded pipe characters are not supported by this simple table parser.

For updates without conflicts, keep personal snippets in an untracked file, for example `my-snippets.local.md`, and set:

```toml
[snippets]
path = "my-snippets.local.md"
```

Paths resolve relative to this installation. Absolute paths work, including synced locations; you control their exposure.

History is plaintext `dictation-log.md`, appended before insertion. Multiline text remains one entry. Set `[log] enabled = false` for memory-only Recents; then history will not survive quitting. Existing files are not erased by disabling logging. Failed recordings are still saved to `recordings/` for recovery; delete them when no longer needed.
