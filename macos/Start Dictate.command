#!/bin/bash
# Double-click to start Dictate in this Terminal window. It uses the permissions
# Terminal already has (Accessibility, Input Monitoring, Microphone).
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
echo "Starting Dictate..."
echo
echo "  Hold  Right Command + Right Option  and speak."
echo "  Release, and your words appear at the cursor, cleaned up."
echo
echo "  To STOP Dictate: close this window (or press Control + C)."
echo "-----------------------------------------------------------------------"
exec "./.venv/bin/python" "dictate.py"
