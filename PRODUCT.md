# Dictate

## Platform

Windows native Python/Tk tray utility. A separate headless macOS implementation by Diane Green remains in `macos/`. It has its own OS integration and verification boundaries.

## User and job

People who dictate into desktop applications and want inspectable source, their own provider keys, and recoverable text. Hold two configured keys, wait for the cue, speak, release, then review the inserted text. Recovery must be available when insertion fails.

## Retained behavior

Windows insertion leaves the clipboard alone. Only deliberately selecting a recent transcript copies it. No Send action, automatic startup, microphone use outside a recording, telemetry, or credentials bundled in releases. Cloud transcription is required; cloud cleanup is optional and off by default. The macOS contribution retains its clipboard-based workflow and is credited separately.

## Design brief

Diane requested the same neutral gray/white/black and restrained blue/teal treatment as Silent Type. Retain the compact tray and Recent dictations interaction. Use native system type, clear states and keyboard access. No personal brand colors or decorative product page. This is a scoped restyle of an existing utility, not a new product flow.

## Release boundaries

MIT source with a Windows setup script and a preserved community macOS port. No signed executable, universal desktop-app compatibility or accessibility certification is promised. Hardware and OS permission checks are distinct from mocked software tests.
