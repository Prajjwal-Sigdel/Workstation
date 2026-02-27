#!/bin/bash
set -e

KWIN_SCRIPT_NAME="sleep-checker-idle"
KWIN_SCRIPTS_DIR="$HOME/.local/share/kwin/scripts"
INSTALL_DIR="$KWIN_SCRIPTS_DIR/$KWIN_SCRIPT_NAME"

echo "=== Sleep Checker - KWin Script Uninstaller ==="
echo ""

# Step 1: Disable the script
echo "[1/3] Disabling script in KWin configuration..."
kwriteconfig6 --file kwinrc --group Plugins --key "${KWIN_SCRIPT_NAME}Enabled" false

# Step 2: Remove script files
echo "[2/3] Removing script files..."
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo "  Removed: $INSTALL_DIR"
else
    echo "  Script directory not found (already removed?)"
fi

# Step 3: Reload KWin scripts
echo "[3/3] Reloading KWin scripts..."
dbus-send --session --type=method_call \
    --dest=org.kde.KWin /Scripting org.kde.kwin.Scripting.start

echo ""
echo "=== Uninstallation Complete ==="