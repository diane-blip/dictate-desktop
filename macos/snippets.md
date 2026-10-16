# Voice snippets

Say the phrase on the left, get the text on the right. One row per snippet; the
file is re-read on every dictation, so edits apply immediately (no restart). The
cleanup pass matches phrases by meaning ("my brand color" still matches "brand
color"), with exact-phrase matching as a fallback when cleanup is off.

Add a row any time you catch yourself repeating something. That's the whole
maintenance story.

| Say | Insert |
|------------|--------------------------|
| my email | you@example.com |
| my website | https://example.com |
| brand color | #3366FF |
