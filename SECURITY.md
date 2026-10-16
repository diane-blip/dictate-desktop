# Security

Do not put API keys, private dictations or recordings in issues or pull requests.

Report suspected exposure or unsafe input behavior privately to **diane@swayrisecreative.com** with a minimal fictional reproduction. Do not send live credentials. There is no guaranteed response time.

Dictate runs with your Windows user's permissions, observes its configured keys and types into applications. It is not a sandbox. Review code and dependencies before installing. API keys and recovery files are local plaintext. Normal Windows insertion does not use the clipboard; explicit Recents copying does.

Use the current Windows release candidate or release. The separate macOS port is community-contributed and has different insertion/privacy behavior. See [privacy](docs/privacy.md) and [release checks](docs/releasing.md).
