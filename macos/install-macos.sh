#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
PYTHON="${PYTHON:-python3.12}"
"$PYTHON" -c 'import sys; assert sys.version_info[:2] == (3, 12), "Use Python 3.12"'
[[ -d .venv ]] || "$PYTHON" -m venv .venv
.venv/bin/python -c 'import sys; assert sys.version_info[:2] == (3, 12), "Use Python 3.12"'
.venv/bin/python -m pip install pip==26.2.1
.venv/bin/python -m pip install --only-binary=:all: --require-hashes -r requirements.lock
.venv/bin/python -m pip check
[[ -f .env ]] || cp .env.example .env
[[ -f config.local.toml ]] || printf '# Local overrides of config.toml.
' > config.local.toml
bash make-app.sh
chmod +x ./*.command
printf '%s
' 'Add your key to .env. Follow README.md for permissions and first use.'
printf '%s
' 'Installation does not launch Dictate or enable login startup.'
