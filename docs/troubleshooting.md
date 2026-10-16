# Troubleshooting

Start from a console with `.venv\Scripts\python.exe dictate.py` to see startup failures. Do not disable antivirus or run as administrator to work around a problem.

| Symptom | Check |
|---|---|
| Nothing starts | Confirm Python 3.12, run `install.ps1`, and inspect `dictate.log`. Another instance, including the personal edition, may hold port 49731. |
| No start cue | Enable microphone access for desktop apps in Windows settings. Check input/output devices and `sounds`. Dictate waits for real microphone frames before the cue. |
| Unexpected microphone | A dead preferred input triggers fallback. Check the selected device name in diagnostics; set `audio.preferred_input` if needed. |
| No text, saved-audio notification | Check internet, provider key, balance/quota and model. Failed WAVs are in `recordings/`; keep them private. |
| Text saved but not inserted | Focus changed, modifiers stayed held, or the target rejected input. Select the transcript in Recents and paste it yourself. |
| Cleanup seems absent | It needs an Anthropic API key and enabled setting. Two-word utterances bypass cleanup. Rejected or failed output falls back; see diagnostics. |
| Certificate failure | Check the system clock and your organization's certificate policy. The locked environment trusts Windows' certificate store. Never disable TLS verification. |
| Git update conflicts | Preserve your edits. Put personal configuration in `config.local.toml` and personal snippets in an untracked file. |

A recording may begin later than the key press while microphone endpoints recover. Start speaking at the cue. Recognition can hallucinate speech from silence/noise; inspect results before using them.

For a useful issue, include Windows/Python versions, commit, expected behavior, actual behavior and a minimal fictional example. Remove keys, transcripts, recordings, identifying device names and private paths from attachments.
