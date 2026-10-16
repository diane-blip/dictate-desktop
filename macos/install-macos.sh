#!/usr/bin/env bash
# Dictate — macOS setup. Run once from this folder:  bash install-macos.sh
# It builds the Python environment and the Dictate.app bundle, then prints the
# one-time permission and login steps (those clicks have to be yours).
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

command -v python3 >/dev/null 2>&1 || { echo "Install Python 3.11+ first (e.g. 'brew install python')."; exit 1; }
echo "Using $(python3 --version)"

[ -d .venv ] || python3 -m venv .venv
echo "Installing dependencies..."
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet -r requirements.txt

[ -f .env ] || { cp .env.example .env; echo "Created .env — add your GROQ_API_KEY to it."; }

bash make-app.sh

cat <<EOF

-------------------------------------------------------------------
Done. Three one-time steps, all yours to do:

1) Add your Groq key (free at https://console.groq.com):
     open -e "$DIR/.env"
   Paste it after GROQ_API_KEY=

2) Grant permissions in System Settings > Privacy & Security. Because the app
   runs THROUGH Python, grant these to the Python at:
     $DIR/.venv/bin/python
       - Accessibility     (add it with the + button)
       - Input Monitoring  (add it with the + button)
   Microphone is prompted the first time you dictate.

3) Start on login:
     - System Settings > General > Login Items > + > add Dictate.app
     - Launch it now:  open "$DIR/Dictate.app"

Control it anytime with Start/Quit/Restart Dictate.command, or run:
  ./.venv/bin/python dictate.py
-------------------------------------------------------------------
EOF
