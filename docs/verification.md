# Release verification

## 0.1.1 · October 16, 2026

45 default Windows tests and all five controlled desktop integration checks passed. Both platform dependency locks passed advisory audits. The macOS source and Diane Green attribution are unchanged; hosted checks cover that port separately.

The implemented gold theme was compared with the approved native previews at normal and constrained sizes, including populated, empty, hover, focus and error states where applicable. Actions are gold with white labels; links and dark-surface focus are light gold; surfaces and selections are neutral gray. White on gold is an approved visual exception, not a claim of AA small-text contrast. Full screen-reader, high-contrast and mixed-DPI support remain unverified.

Release assets are built from the exact commit, with hosted checks, exported-tree/history secret scans and an unauthenticated SHA-256 download check recorded in the versioned release notes. Existing personal installations are not modified.

## Previous release evidence


Dictate 0.1.0, October 15, 2026. Windows x64 / Python 3.12 is the primary tested desktop target. macOS keeps its separate contributed implementation.

## Windows evidence

The local release checks include 50 tests with all controlled Windows integration tests enabled, zero skips. They exercise real Unicode insertion into an owned test editor, clipboard sequence preservation, deliberate popup copying, durable recovery before insertion, microphone failure/retry, bounded capture, incomplete-audio recovery, menu/focus guards, provider failure handling, configuration validation, and actual Anthropic SDK behavior through a mock HTTP transport.

The runtime was installed into a fresh virtual environment using the complete hashed lock. Development tools have their own universal hashed lock. Native popup captures cover populated, empty and ten-entry states with fictional text. Tests verify scrolling in a simulated 1024 × 768 work area at 150% scaling and real absolute window placement at negative desktop coordinates. A separate Impeccable finish review found no remaining material issues in that popup scope.

Local acceptance also opened the real microphone, captured one second of audio and closed it without saving or uploading the recording; created and closed the real tray with global hotkeys disabled; and verified shortcut creation, removal and refusal to overwrite a foreign shortcut in an isolated folder. Runtime dependency audits found no known advisories on October 15, 2026.

## macOS scope

All 13 macOS regressions passed on an Apple Silicon GitHub runner, including actual disposable-process inspection and shutdown while an unrelated process remained alive. The locked installer, package consistency, dependency audit, shell syntax and generated app-bundle metadata also passed. The tests use a dummy keyboard backend and mocked provider/clipboard operations. These checks do not constitute a real user's microphone, permissions, clipboard, or app-bundle acceptance.

The hosted [Checks workflow](https://github.com/diane-blip/dictate-desktop/actions/workflows/checks.yml) repeats platform software checks on each main push and pull request. Its Windows job intentionally skips the five interactive tests; the local desktop run above includes all five. Release assets come from the exact tested commit, with a separate SHA-256 file and an unauthenticated download check.

## Boundaries

Cloud calls in the automated suite are mocked; no provider availability or billing guarantee follows. Windows input checks use a controlled Tk editor, not every desktop application. Foreground-window guards cannot detect a different field inside the same window or make insertion atomic. macOS has a separate clipboard path without that destination guard.

No second-PC, broad hardware, screen-reader, multi-monitor or high-DPI certification. The custom Windows canvas popup does not expose native list semantics to screen readers. The distribution is source plus setup scripts, not a signed executable. AI cleanup is opt-in and remains probabilistic. Dependencies are checked for known advisories, not certified free of security defects.
