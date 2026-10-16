# Privacy and provider costs

Dictate has no hosted account, subscription, telemetry endpoint or automatic updater. It does use external speech/AI APIs under your accounts.

| Data | Destination |
|---|---|
| Captured audio | Groq by default, or OpenAI if selected |
| Transcript and the full snippet table | Anthropic only after cleanup is explicitly enabled and a key is present |
| Completed transcript | Foreground application, in-memory Recents, and local Markdown history by default |
| Audio when transcription or capture fails | Local `recordings/` folder |
| Keys | Your untracked `.env` or process environment |
| Diagnostic events | Local rotating `dictate.log`, up to three approximately 1MB files |

Successful recordings are held in memory, not written as audio files by the Windows app. Provider retention and processing rules still apply. Local history and saved failed audio are **not encrypted by Dictate**. Other software, backups or sync tools with access to the folder can read them.

Only record material you intend to send to the chosen provider. Avoid secrets in snippets: the entire table reaches Anthropic during cleanup. Provider error bodies are excluded from transcription diagnostics, but inspect logs before attaching them to an issue.

Software is MIT licensed. API use may cost money and is subject to account limits. A ChatGPT or Claude chat subscription does not itself establish access or billing for these calls. Consult current provider terms and your account:

- [Groq transcription and limits](https://console.groq.com/docs/speech-to-text)
- [OpenAI API pricing](https://openai.com/api/pricing/)
- [Anthropic API pricing](https://platform.claude.com/docs/en/about-claude/pricing)

Normal Windows dictation never reads or writes the clipboard. Clicking a Recents entry replaces its contents. Windows clipboard history/sync may retain that copied transcript under your system settings.

The community macOS port has different behavior: it uses the clipboard for insertion and can restore text only. See its README before use.
