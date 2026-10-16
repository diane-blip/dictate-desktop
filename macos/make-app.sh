#!/usr/bin/env bash
# Build Dictate.app — a minimal bundle that launches the app with a real bundle
# identity, so macOS gives it a menu bar item and attributes permissions to
# "Dictate" (not Terminal). Re-run this after moving the folder.
#
# NOT code-signed on purpose: ad-hoc signing a Python app makes macOS enforce
# library validation, which then refuses to load the venv's (differently-signed)
# native extensions and the app dies silently on launch. Unsigned + not
# quarantined (a locally built app) launches fine on Apple Silicon.
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE="$APP_DIR/Dictate.app"

rm -rf "$BUNDLE"
mkdir -p "$BUNDLE/Contents/MacOS"

cat > "$BUNDLE/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>Dictate</string>
    <key>CFBundleDisplayName</key><string>Dictate</string>
    <key>CFBundleIdentifier</key><string>com.example.dictate</string>
    <key>CFBundleExecutable</key><string>Dictate</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleVersion</key><string>1.0</string>
    <key>CFBundleShortVersionString</key><string>1.0</string>
    <key>LSMinimumSystemVersion</key><string>12.0</string>
    <key>LSUIElement</key><true/>
    <key>NSMicrophoneUsageDescription</key>
    <string>Dictate records your voice while you hold the hotkey, so it can transcribe what you say.</string>
</dict>
</plist>
PLIST

# Launcher: run the project's venv Python on dictate.py, sending any startup
# output to dictate-launch.log so a crash-on-launch is visible. APP_DIR is baked
# in at build time; runtime $DIR references stay literal.
cat > "$BUNDLE/Contents/MacOS/Dictate" <<LAUNCH
#!/bin/bash
DIR="$APP_DIR"
cd "\$DIR"
exec "\$DIR/.venv/bin/python" "\$DIR/dictate.py" >> "\$DIR/dictate-launch.log" 2>&1
LAUNCH
chmod +x "$BUNDLE/Contents/MacOS/Dictate"

# Strip extended attributes so nothing trips up LaunchServices. Do NOT sign.
xattr -cr "$BUNDLE" 2>/dev/null || true

echo "Built: $BUNDLE (unsigned)"
echo "Launch with:  open \"$BUNDLE\""
