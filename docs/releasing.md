# Release checks

A green CI run proves automated checks, not microphone quality or compatibility with every desktop app.

1. Review the full diff, attribution, license, current tree and every commit that will become public. Scan history for secrets and private data.
2. Run lint, formatting and offline regression tests on Windows/Python 3.12. Run dependency audit against the locked distribution.
3. Install the exact candidate in a fresh folder/environment using the README. Check required-key errors and all imports. Preserve the existing user's settings on an update.
4. In a controlled editor, verify real Unicode/emoji/multiline insertion and unchanged clipboard sequence; verify opening/dismissing Recents and explicit selection. Repeat with a copied image and a copied file when certifying those manual cases.
5. Verify real microphone start/stop and failover on available hardware, the recording cap, denied microphone access, network failure, rejected input, disk-write failure and invalid reload. Mocked failure cases are labeled as such.
6. Run a live synthetic-audio provider check using private test credentials. Never store keys or actual user speech in artifacts.
7. Check optional shortcuts with `-WhatIf`, install/remove them in an isolated Windows profile before claiming that acceptance. Do not overwrite someone else's installation.
8. Review README/privacy/known limits and the exact launch copy. Get the owner's approval before making the repository public, tagging a public release or posting.

macOS requires a separate maintainer/device acceptance pass. Syntax checks alone are insufficient.
