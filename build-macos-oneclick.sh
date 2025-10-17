#!/bin/bash
# One-Click macOS Build Script for Turnkey Coach Tools
# Creates a true one-click experience that opens in iTerm/Terminal

set -e

VERSION="1.5.0"
OUTPUT_DIR="dist/macos-oneclick"
APP_NAME="TurnkeyCoachTools"
BUNDLE_ID="com.karlschudt.turnkey-coach-tools"

echo "=== Turnkey Coach Tools - One-Click macOS Build ==="
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

# Create app bundle structure
APP_BUNDLE="$OUTPUT_DIR/$APP_NAME.app"
CONTENTS_DIR="$APP_BUNDLE/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

echo "Creating optimized app bundle structure..."

# Create enhanced Info.plist with icon support
cat > "$CONTENTS_DIR/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleDisplayName</key>
    <string>Turnkey Coach Tools</string>
    <key>CFBundleExecutable</key>
    <string>turnkey-coach</string>
    <key>CFBundleIdentifier</key>
    <string>com.karlschudt.turnkey-coach-tools</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>TurnkeyCoachTools</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
<key>CFBundleShortVersionString</key>
    <string>1.5.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.utilities</string>
    <key>LSArchitecturePriority</key>
    <array>
        <string>arm64</string>
        <string>x86_64</string>
    </array>
    <key>LSMinimumSystemVersionByArchitecture</key>
    <dict>
        <key>arm64</key>
        <string>11.0</string>
        <key>x86_64</key>
        <string>10.15</string>
    </dict>
    <key>CFBundleIconFile</key>
    <string>app-icon.icns</string>
    <key>NSAppleScriptEnabled</key>
    <false/>
    <key>LSEnvironment</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>$APP_BUNDLE/Contents/Resources</string>
    </dict>
</dict>
</plist>
EOF

# Create the enhanced launcher script that opens iTerm
cat > "$MACOS_DIR/turnkey-coach" << 'EOF'
#!/bin/bash
# Turnkey Coach Tools - One-Click Launcher (iTerm + Terminal)

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
RESOURCES_DIR="$APP_DIR/Contents/Resources"

# Set up environment
export PYTHONPATH="$RESOURCES_DIR:$PYTHONPATH"
cd "$RESOURCES_DIR"

# Function to show user-friendly error dialogs
show_error() {
    osascript -e "display dialog \"$1\" with title \"Turnkey Coach Tools\" buttons {\"OK\"} default button 1 with icon stop"
}

show_info() {
    osascript -e "display dialog \"$1\" with title \"Turnkey Coach Tools\" buttons {\"OK\"} default button 1 with icon note giving up after 3"
}

# Check if Python 3 is installed
if ! command -v python3 >/dev/null 2>&1; then
    show_error "Python 3 is required but not installed.\n\nPlease install Python 3.8 or later from python.org and try again."
    exit 1
fi

# Check Python version
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" 2>/dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))" 2>/dev/null || echo "unknown")
    show_error "Python $PYTHON_VERSION found, but Python 3.8 or later is required.\n\nPlease install Python 3.8+ from python.org and try again."
    exit 1
fi

# Install dependencies if needed
if [ ! -f "$RESOURCES_DIR/.deps_installed" ]; then
    show_info "Installing dependencies... This may take a moment.\n\nPlease wait while we set up your environment."
    
    if python3 -m pip install -r "$RESOURCES_DIR/requirements.txt" --user --quiet; then
        touch "$RESOURCES_DIR/.deps_installed"
    else
        show_error "Failed to install dependencies.\n\nPlease check your internet connection and try again."
        exit 1
    fi
fi

# Function to launch in iTerm
launch_iterm() {
    osascript <<APPLESCRIPT
tell application "iTerm"
    activate
    try
        set newWindow to (create window with default profile)
        tell current session of newWindow
            write text "cd '$RESOURCES_DIR' && python3 coach_cli.py"
            set name to "Turnkey Coach Tools"
        end tell
    on error
        -- Fallback for older iTerm versions
        tell current window
            create tab with default profile
            tell current session
                write text "cd '$RESOURCES_DIR' && python3 coach_cli.py"
                set name to "Turnkey Coach Tools"
            end tell
        end tell
    end try
end tell
APPLESCRIPT
}

# Function to launch in Terminal (fallback)
launch_terminal() {
    osascript <<APPLESCRIPT
tell application "Terminal"
    activate
    set newTab to do script "cd '$RESOURCES_DIR' && python3 coach_cli.py"
    set custom title of newTab to "Turnkey Coach Tools"
end tell
APPLESCRIPT
}

# Try to launch in iTerm first, then fallback to Terminal
if command -v iTerm >/dev/null 2>&1 || [ -d "/Applications/iTerm.app" ]; then
    launch_iterm || launch_terminal
else
    launch_terminal
fi
EOF

chmod +x "$MACOS_DIR/turnkey-coach"

# Copy app icon if it exists
if [ -f "app-icon.icns" ]; then
    cp "app-icon.icns" "$RESOURCES_DIR/"
    echo "✓ Copied custom app icon"
else
    echo "⚠ No app icon found (create app-icon.icns for custom icon)"
fi

# Copy Python application files to Resources
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
    "bulk_sync.py"
    "requirements.txt"
    "exerciselist.json"
    "README.md"
    "WARP.md"
)

for file in "${PYTHON_FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$RESOURCES_DIR/"
        echo "  ✓ $file"
    else
        echo "  ⚠ $file not found"
    fi
done

echo ""
echo "✅ App bundle created: $APP_BUNDLE"

# Remove quarantine attributes to prevent Gatekeeper issues
echo "Preparing app bundle for distribution..."
xattr -cr "$APP_BUNDLE"
chmod -R 755 "$APP_BUNDLE"
chmod +x "$APP_BUNDLE/Contents/MacOS/turnkey-coach"

# Create drag-and-drop installer DMG
echo "Creating drag-and-drop installer..."

# Create temporary DMG directory
DMG_DIR="$OUTPUT_DIR/dmg-temp"
mkdir -p "$DMG_DIR"

# Copy app to DMG directory
cp -R "$APP_BUNDLE" "$DMG_DIR/"

# Copy the smart installer
cp "install-and-launch.sh" "$DMG_DIR/"
chmod +x "$DMG_DIR/install-and-launch.sh"

# Create a Applications folder shortcut in DMG
ln -s /Applications "$DMG_DIR/Applications"

# Create DMG background and instructions
cat > "$DMG_DIR/INSTALL.txt" << 'EOF'
TURNKEY COACH TOOLS - INSTALLATION GUIDE
=========================================

📦 STEP 1: Install the App
1. Drag "TurnkeyCoachTools.app" to the "Applications" folder
2. Wait for the copy to complete

🚀 STEP 2: First Launch
1. Open Applications folder (Finder → Applications)
2. Find "TurnkeyCoachTools" 
3. RIGHT-CLICK the app and select "Open"
4. Click "Open" in the security dialog

⚠️  IMPORTANT: Use RIGHT-CLICK → Open for first launch!
   This bypasses macOS security for unsigned apps.
   After the first launch, you can double-click normally.

✅ What happens when launched:
- Opens in iTerm or Terminal automatically
- Installs dependencies on first run (internet required)
- Launches the coaching tools CLI interface
- No technical knowledge needed!

🔧 If you get security warnings:
1. System Preferences → Security & Privacy
2. Click "Open Anyway" if prompted
3. Or use: Right-click app → Open → Open

For support, contact your developer.
EOF

# Create the DMG
DMG_NAME="TurnkeyCoachTools-$VERSION-Installer"
DMG_PATH="$OUTPUT_DIR/$DMG_NAME.dmg"

if command -v hdiutil >/dev/null 2>&1; then
    # Create DMG
    hdiutil create -volname "$DMG_NAME" -srcfolder "$DMG_DIR" -ov -format UDZO "$DMG_PATH"
    
    # Clean up temp directory
    rm -rf "$DMG_DIR"
    
    if [ -f "$DMG_PATH" ]; then
        echo "✅ DMG installer created: $DMG_PATH"
    else
        echo "❌ Failed to create DMG installer"
    fi
else
    echo "⚠ hdiutil not available, skipping DMG creation"
    echo "✅ Manual install folder available: $DMG_DIR"
fi

# Also create a simple ZIP for easy distribution
ZIP_NAME="TurnkeyCoachTools-$VERSION-macOS"
ZIP_PATH="$OUTPUT_DIR/$ZIP_NAME.zip"

if command -v zip >/dev/null 2>&1; then
    cd "$OUTPUT_DIR"
    zip -r "$ZIP_NAME.zip" "$APP_NAME.app" > /dev/null
    cd "$SCRIPT_DIR"
    echo "✅ ZIP archive created: $ZIP_PATH"
fi

# Create distribution README
cat > "$OUTPUT_DIR/README-Distribution.md" << EOF
# Turnkey Coach Tools - macOS Distribution

## For End Users (Coaches)

### Quick Install (Recommended)
1. Download \`$DMG_NAME.dmg\`
2. Double-click to open
3. Drag "TurnkeyCoachTools.app" to "Applications" folder
4. Launch from Applications folder or Spotlight

### Alternative Install
1. Download \`$ZIP_NAME.zip\`
2. Extract the zip file
3. Drag "TurnkeyCoachTools.app" to Applications folder
4. Launch from Applications folder or Spotlight

## What Happens When Launched

1. **First Run**: App will install Python dependencies (internet required)
2. **Subsequent Runs**: App launches immediately
3. **Interface**: Opens in iTerm (or Terminal) with full CLI experience
4. **No Technical Knowledge Required**: Everything is automated

## User Experience

- **One-click launch** from Applications folder or Spotlight
- **Automatic dependency management** 
- **Native terminal experience** in iTerm/Terminal
- **No command line knowledge needed**
- **Works on both Intel and Apple Silicon Macs**

## System Requirements

- macOS 10.15 (Catalina) or later
- Python 3.8+ (will prompt to install if missing)
- Internet connection (for first-time setup only)

## Distribution

Simply share the DMG or ZIP file with coaches. No additional instructions needed!

Build Date: $(date)
Version: $VERSION
EOF

echo ""
echo "🎉 ONE-CLICK BUILD COMPLETE!"
echo ""
echo "📦 Distribution Files:"
if [ -f "$DMG_PATH" ]; then
    echo "  🔥 $DMG_NAME.dmg (recommended for distribution)"
fi
if [ -f "$ZIP_PATH" ]; then
    echo "  📁 $ZIP_NAME.zip (alternative distribution)"
fi
echo "  📱 $APP_NAME.app (the actual application)"
echo "  📖 README-Distribution.md (distribution guide)"
echo ""
echo "🚀 Ready for Distribution!"
echo "   Simply share the DMG file with coaches."
echo "   They drag-and-drop to install, then double-click to run!"
echo ""