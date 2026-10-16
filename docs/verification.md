# Windows release-candidate verification

Verified October 15, 2026, on Windows with CPython 3.12.10.

| Check | Result |
|---|---|
| Regression suite, including opt-in interactive checks | 41 passed, zero skipped |
| Same suite in a fresh installation from the hashed lock | 41 passed, zero skipped |
| Lint and formatting | Passed |
| Dependency consistency | Passed in development and clean runtime environments |
| Locked runtime vulnerability audit | No known vulnerabilities reported by pip-audit 2.10.1 |
| Existing Git history secret scan | No leaks reported by Gitleaks 8.30.1 |
| Exact source-only export secret scan | No leaks reported |
| Documentation links and PowerShell syntax | Passed |
| Real tray/Tk lifecycle | Started, polled unused test keys, quit and joined polling thread |
| Real microphone capture | Valid 16kHz mono PCM; brief audio kept in memory, neither saved nor uploaded |
| Live Groq transcription | Fictional synthesized speech transcribed successfully |
| Live Anthropic cleanup | Completed response; punctuation applied to a fictional phrase |
| Existing-installation shortcut protection | Refused conflicting shortcut; existing shortcut hash unchanged |

Interactive tests inserted smart punctuation, emoji and multiline text in a controlled editor while checking that the clipboard sequence number stayed unchanged. Recents opening, dismissal and explicit row selection were exercised; the copy callback was mocked so the test did not replace the user's clipboard. Other tests cover stale focus, held modifiers, recovery on failure, malformed/provider-error responses, incomplete cleanup, invalid configuration, history, snippets and lifecycle guards.

The latest dependency compatibility test exposed a recursion error between a global certificate helper and the current Anthropic client. The helper was removed. Both providers now receive explicit system-certificate SSL contexts; the fresh installation and live checks ran after that change.

## Limits of this evidence

- Hosted CI is not active. The prepared workflow is [ci-windows.yml](ci-windows.yml); existing repository access could save the code but could not install a workflow. All results above are local checks, not a GitHub Actions run.
- Provider calls used fictional generated speech/text. They do not establish recognition accuracy for every accent, microphone or environment.
- Microphone failover, disk/network failure and configuration conflicts include mocked failure cases. Not every physical device failure was reproduced.
- Foreground ownership was established for the test editor before input; tests abort rather than type into another window.
- No second physical Windows machine, administrator-target application or complete desktop-app compatibility matrix was tested.
- Shortcut conflict protection and script syntax were verified. Creating/removing startup shortcuts in a fresh Windows user profile remains a manual release check.
- macOS syntax was checked. Its runtime and dependencies were not certified by these Windows results.
- No repository visibility change, public tag, release upload or social post is authorized by this record.
