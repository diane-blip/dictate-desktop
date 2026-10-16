# Release verification

Dictate 0.1.0, October 15, 2026. Windows x64 / Python 3.12 is the primary tested desktop target. macOS keeps its separate contributed implementation.

## Windows evidence

The local release checks include 50 tests with all controlled Windows integration tests enabled, zero skips. They exercise real Unicode insertion into an owned test editor, clipboard sequence preservation, deliberate popup copying, durable recovery before insertion, microphone failure/retry, bounded capture, incomplete-audio recovery, menu/focus guards, provider failure handling, configuration validation, and actual Anthropic SDK behavior through a mock HTTP transport.

The runtime was installed into a fresh virtual environment using the complete hashed lock. Development tools have their own universal hashed lock. Native popup captures cover populated, empty and ten-entry states with fictional text. Tests verify scrolling in a simulated 1024 × 768 work area at 150% scaling and real absolute window placement at negative desktop coordinates. A separate Impeccable finish review found no remaining material issues in that popup scope.

Local acceptance also opened the real microphone, captured one second of audio and closed it without saving or uploading the recording; created and closed the real tray with global hotkeys disabled; and verified shortcut creation, removal and refusal to overwrite a foreign shortcut in an isolated folder. Runtime dependency audits found no known advisories on October 15, 2026.

## macOS scope

The contributed code is maintained and credited, with dedicated regression tests and a macOS CI job. Its tests use a dummy keyboard backend and mocked provider/clipboard operations. The process-control test uses actual disposable processes on the macOS runner. These checks do not constitute a real user's microphone, permissions, clipboard, or app-bundle acceptance.

## Boundaries

Cloud calls in the automated suite are mocked; no provider availability or billing guarantee follows. Windows input checks use a controlled Tk editor, not every desktop application. Foreground-window guards cannot detect a different field inside the same window or make insertion atomic. macOS has a separate clipboard path without that destination guard.

No second-PC, broad hardware, screen-reader, multi-monitor or high-DPI certification. The custom Windows canvas popup does not expose native list semantics to screen readers. The distribution is source plus setup scripts, not a signed executable. AI cleanup is opt-in and remains probabilistic. Dependencies are checked for known advisories, not certified free of security defects.
