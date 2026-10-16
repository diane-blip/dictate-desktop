# Release procedure

1. Verify the intended source and a clean checkout. Preserve the macOS contribution and AUTHORS.md. Run each platform's software tests and the Windows integration checks; record any untested hardware or permission paths honestly.
2. Run lint/formatting, package consistency and audits of both runtime locks. Check PowerShell and shell syntax, local documentation links and the real popup states. Inspect the diff for machine paths, private samples and unwanted dependencies.
3. Scan the complete public Git history and exported source for secrets. Never archive a working directory containing environments, keys, recordings or logs.
4. Commit and push the intended main branch. Require successful GitHub checks for that exact commit. Create the source ZIP with `git archive`, include both platform sources and licenses, and calculate SHA-256.
5. Create a versioned GitHub release at that commit, attach the source ZIP and `SHA256SUMS.txt`, and state the verification limits. Download the published ZIP without authentication and verify its hash. Confirm the release tag, main and local HEAD agree.

No automatic publishing credentials or workflow are required. Releases are deliberate maintainer actions. Model/provider changes require testing the exact current request shape; never use real private transcripts as fixtures.
