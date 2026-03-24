#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_LABEL="com.claude.noteswatcher"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_LABEL.plist"

mkdir -p "$HOME/Library/LaunchAgents"

if [ -f "$PLIST_DEST" ]; then
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

cat > "$PLIST_DEST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>-m</string>
        <string>watcher</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>StartInterval</key>
    <integer>60</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/watcher.log</string>
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/watcher.log</string>
</dict>
</plist>
EOF

launchctl load "$PLIST_DEST"
echo "Notes Watcher installed. Running every 60 seconds."
echo "Logs: $SCRIPT_DIR/watcher.log"
