#!/bin/bash
pkill -f dictate.py && echo "Dictate stopped." || echo "Dictate was not running."
echo "You can close this window."
