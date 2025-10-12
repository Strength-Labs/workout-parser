#!/bin/bash
# Simple Launcher Build Script - Bypasses macOS App Bundle Security Issues
# Creates a simple executable that launches in Terminal

set -e

VERSION="1.0.0"
OUTPUT_DIR="dist/simple-launcher"
LAUNCHER_NAME="turnkey-coach"

echo "=== Turnkey Coach Tools - Simple Launcher Build ==="
echo "Version: $VERSION"
echo ""

# Ensure we're in the right directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Clean and create output directory
if [ -d "$OUTPUT_DIR" ]; then
    rm -rf "$OUTPUT_DIR"
fi
mkdir -p "$OUTPUT_DIR"

echo "Creating simple terminal launcher..."

# Create the launcher script
cat > "$OUTPUT_DIR/$LAUNCHER_NAME" << 'EOF'
#!/bin/bash
# Turnkey Coach Tools - Simple Terminal Launcher

# Get the directory containing this script
LAUNCHER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set up environment
export PYTHONPATH="$LAUNCHER_DIR:$PYTHONPATH"
cd "$LAUNCHER_DIR"

# Function to show user-friendly messages
show_message() {
    echo ""
    echo "==============================================="
    echo "  $1"
    echo "==============================================="
    echo ""
}

# Check if Python 3 is installed
if ! command -v python3 >/dev/null 2>&1; then
    show_message "Python 3 is required but not installed"
    echo "Please install Python 3.8 or later from python.org"
    echo "Then try running this script again."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check Python version
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" 2>/dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))" 2>/dev/null || echo "unknown")
    show_message "Python $PYTHON_VERSION found, but Python 3.8+ required"
    echo "Please install Python 3.8 or later from python.org"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Install dependencies if needed
if [ ! -f "$LAUNCHER_DIR/.deps_installed" ]; then
    show_message "First-time setup - Installing dependencies"
    echo "This may take a moment..."
    echo ""
    
    if python3 -m pip install -r "$LAUNCHER_DIR/requirements.txt" --user --quiet; then
        touch "$LAUNCHER_DIR/.deps_installed"
        echo "Dependencies installed successfully!"
    else
        show_message "Failed to install dependencies"
        echo "Please check your internet connection and try again."
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo ""
fi

# Launch the application
show_message "Launching Turnkey Coach Tools"
python3 coach_cli.py
EOF

chmod +x "$OUTPUT_DIR/$LAUNCHER_NAME"

# Copy all Python files
echo "Copying application files..."
PYTHON_FILES=(
    "coach_cli.py"
    "api_client.py"
    "settings.py"
    "directory_migration.py"
    "encoding_utils.py"
    "feed_tool.py"
    "pr_tool.py"
    "actual_prs_tool.py"
    "format_tool.py"
    "upload_tool.py"
    "ai_chat_tool.py"
    "requirements.txt"
    "exerciselist.json"
    "README.md"
    "WARP.md"
)

for file in "${PYTHON_FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$OUTPUT_DIR/"
        echo "  ✓ $file"
    else
        echo "  ⚠ $file not found"
    fi
done

# Create a DMG with simple instructions
echo ""
echo "Creating simple distribution package..."

DMG_DIR="$OUTPUT_DIR/dmg-temp"
mkdir -p "$DMG_DIR"

# Copy all files to DMG
cp -R "$OUTPUT_DIR"/* "$DMG_DIR/"
rm -rf "$DMG_DIR/dmg-temp" 2>/dev/null || true

# Create simple instructions
cat > "$DMG_DIR/HOW-TO-INSTALL.txt" << 'EOF'
TURNKEY COACH TOOLS - SIMPLE INSTALLATION
==========================================

🚀 SUPER EASY SETUP:

1. Copy the "turnkey-coach" file to your Desktop
2. Double-click "turnkey-coach" to launch
3. That's it!

The first time you run it:
- It will install dependencies automatically
- This requires internet connection
- May take 1-2 minutes

After first run:
- Double-click launches immediately
- No internet required
- Full coaching tools interface

💡 TIPS:
- Keep the "turnkey-coach" file anywhere you want
- You can move it to Applications if desired
- Works by double-clicking in Finder
- No complex installation needed!

🔧 REQUIREMENTS:
- Python 3.8+ (will prompt if missing)
- Internet (for first-time setup only)
- macOS 10.15+ recommended

For support, contact your developer.
EOF

# Create the DMG
DMG_NAME="TurnkeyCoachTools-$VERSION-Simple"
DMG_PATH="$OUTPUT_DIR/$DMG_NAME.dmg"

if command -v hdiutil >/dev/null 2>&1; then
    hdiutil create -volname "$DMG_NAME" -srcfolder "$DMG_DIR" -ov -format UDZO "$DMG_PATH"
    rm -rf "$DMG_DIR"
    
    if [ -f "$DMG_PATH" ]; then
        echo "✅ Simple DMG created: $DMG_PATH"
    fi
fi

# Also create ZIP
ZIP_NAME="TurnkeyCoachTools-$VERSION-Simple"
ZIP_PATH="$OUTPUT_DIR/$ZIP_NAME.zip"

if command -v zip >/dev/null 2>&1; then
    cd "$OUTPUT_DIR"
    zip -r "$ZIP_NAME.zip" * -x "*.dmg" "dmg-temp/*" > /dev/null
    cd "$SCRIPT_DIR"
    echo "✅ Simple ZIP created: $ZIP_PATH"
fi

echo ""
echo "🎉 SIMPLE LAUNCHER BUILD COMPLETE!"
echo ""
echo "📦 Distribution Files:"
echo "  🔥 $DMG_NAME.dmg (drag-and-drop distribution)"
echo "  📁 $ZIP_NAME.zip (extract and double-click)"
echo "  🚀 $LAUNCHER_NAME (the launcher executable)"
echo ""
echo "✨ COACH-FRIENDLY EXPERIENCE:"
echo "   1. Share the DMG or ZIP file"
echo "   2. Coaches double-click 'turnkey-coach' to run"
echo "   3. No app installation, no security warnings!"
echo "   4. Works from anywhere on their Mac!"
echo ""