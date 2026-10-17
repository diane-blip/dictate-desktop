# Authors and contribution history

- **Diane Whiddon** ([dianewhiddon](https://github.com/dianewhiddon)): original Windows Dictate application and maintenance.
- **Diane Green** ([dianegreendesign](https://github.com/dianegreendesign)): the community macOS port, including its headless workflow, held keys, clipboard insertion, Groq cleanup, app bundle and control scripts. Original contribution: `7ddb28d27844c9d8b5b3b523f08ac5aeddd0f8ff`, merged August 3, 2026 through [member repository PR #1](https://github.com/SRC-Rabbit-Hole/dictate-starter/pull/1), merge `e5c51912b8246e36185fa7015546d9dff1939511`. That repository may require member access.

This public repository starts from the member edition at `c35f422747544804b124c009a26cd6e4ffa10856`. It preserves the contributed implementation under `macos/`; it does not claim the port as Diane Whiddon's work. The new repository excludes private installation data and has its own release history.

The public release adds neutral Windows styling, bounded capture and recovery, dependency locks, automated checks, and targeted macOS maintenance: the missing sound module, save-before-paste, complete-response validation, clipboard failure cleanup, and installation-specific process control. These changes do not replace the original contribution credit. See [CHANGELOG.md](CHANGELOG.md) and each platform's verification limits.
