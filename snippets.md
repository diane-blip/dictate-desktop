# Voice snippets

Say the phrase on the left, get the text on the right. One row per snippet; the file is re-read on every dictation, so edits apply immediately. The cleanup pass matches phrases semantically ("my brand pink color" still matches "brand pink"), and there's exact-phrase matching as a fallback when the cleanup pass is off.

| Say | Insert |
|------------|---------|
| brand pink | #F49CBB |
| my email | you@example.com |
| my site | https://example.com |
