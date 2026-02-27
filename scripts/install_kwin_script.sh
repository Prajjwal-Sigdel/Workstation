#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
KWIN_SCRIPT_NAME="sleep-checker-idle"
KWIN_SCRIPTS_DIR="$HOME/.local/share/kwin/scripts"
INSTALL_DIR="$KWIN_SCRIPTS_DIR/$KWIN_SCRIPT_NAME"

echo "=== Sleep Checker - KWin Script Installer ==="
echo ""

# Step 1: Create target directory
echo "[1/4] Creating KWin scripts directory..."
mkdir -p "$INSTALL_DIR"

# Step 2: Copy script files
echo "[2/4] Copying script files..."
cp -r "$PROJECT_DIR/kwin-scripts/$KWIN_SCRIPT_NAME/"* "$INSTALL_DIR/"
echo "  Installed to: $INSTALL_DIR"

# Step 3: Enable the script in KWin config
echo "[3/4] Enabling script in KWin configuration..."
kwriteconfig6 --file kwinrc --group Plugins --key "${KWIN_SCRIPT_NAME}Enabled" true

# Step 4: Reload KWin scripts
echo "[4/4] Reloading KWin scripts..."
dbus-send --session --type=method_call \
    --dest=org.kde.KWin /Scripting org.kde.kwin.Scripting.start

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Verification:"
echo "  1. Check installed: ls $INSTALL_DIR"
echo "  2. Check enabled:   kreadconfig6 --file kwinrc --group Plugins --key ${KWIN_SCRIPT_NAME}Enabled"
echo "  3. Monitor signal:  dbus-monitor --session \"type='signal',interface='org.sleepchecker.IdleNotifier'\""
echo ""
echo "Let your screen dim from inactivity to test the signal."