#!/usr/bin/env bash
# Build an unsigned local launcher. No signing or permission changes.
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE="$APP_DIR/Dictate.app"
for path in "$BUNDLE" "$BUNDLE/Contents" "$BUNDLE/Contents/MacOS"; do
    [[ ! -L "$path" ]] || { echo "Refusing symlinked bundle path: $path" >&2; exit 1; }
done
mkdir -p "$BUNDLE/Contents/MacOS"
cat > "$BUNDLE/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleName</key><string>Dictate</string>
<key>CFBundleIdentifier</key><string>io.github.diane-blip.dictate</string>
<key>CFBundleExecutable</key><string>Dictate</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleVersion</key><string>0.1.0</string>
<key>CFBundleShortVersionString</key><string>0.1.0</string>
<key>LSMinimumSystemVersion</key><string>12.0</string>
<key>LSUIElement</key><true/>
<key>NSMicrophoneUsageDescription</key><string>Record audio while you hold the dictation keys.</string>
</dict></plist>
PLIST
cat > "$BUNDLE/Contents/MacOS/Dictate" <<'LAUNCH'
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$DIR"
exec "$DIR/.venv/bin/python" "$DIR/dictate.py" >> "$DIR/dictate-launch.log" 2>&1
LAUNCH
chmod +x "$BUNDLE/Contents/MacOS/Dictate"
echo "Built unsigned local launcher: $BUNDLE"
