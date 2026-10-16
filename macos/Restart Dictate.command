#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pkill -f dictate.py 2>/dev/null
sleep 1
open "$DIR/Dictate.app"
echo "Dictate restarted. You can close this window."
