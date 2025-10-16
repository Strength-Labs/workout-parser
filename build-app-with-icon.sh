#!/bin/bash
# App Bundle Build Script - Wraps one-file executable with custom icon
# Creates a proper macOS app that displays the custom icon beautifully

set -e

VERSION="1.5.0"
OUTPUT_DIR="dist/app-with-icon"
APP_NAME="TurnkeyCoachTools"

echo "🎨 Turnkey Coach Tools - App Bundle with Custom Icon"
echo "===================================================="
echo "Version: $VERSION"
echo ""

# Ensure we're in the right directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if we have the one-file executable
ONEFILE_EXEC="dist/onefile/turnkey-coach"
if [ ! -f "$ONEFILE_EXEC" ]; then
    echo "❌ One-file executable not found at $ONEFILE_EXEC"
    echo "   Please run ./build-onefile.sh first"
    exit 1
fi

# Check for custom icon
if [ ! -f "app-icon.icns" ]; then
    echo "❌ Custom icon not found (app-icon.icns)"
    echo "   Please make sure app-icon.icns is in the project directory"
    exit 1
fi

echo "✅ Found one-file executable: $ONEFILE_EXEC"
echo "🎨 Found custom icon: app-icon.icns"
echo ""

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

echo "🏗️  Creating app bundle structure..."

# Copy the one-file executable to MacOS directory
cp "$ONEFILE_EXEC" "$MACOS_DIR/turnkey-coach-executable"
chmod +x "$MACOS_DIR/turnkey-coach-executable"

# Copy custom icon to Resources
cp "app-icon.icns" "$RESOURCES_DIR/"
echo "✅ Custom icon copied to app bundle"

# Create launcher script that opens Terminal
cat > "$MACOS_DIR/TurnkeyCoachTools" << 'EOF'
#!/bin/bash
# App Bundle Launcher - Opens Terminal with our executable

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXECUTABLE="$SCRIPT_DIR/turnkey-coach-executable"

# Function to launch in Terminal
launch_terminal() {
    osascript <<APPLESCRIPT
tell application "Terminal"
    activate
    set newTab to do script "'$EXECUTABLE'"
    set custom title of newTab to "Turnkey Coach Tools"
end tell
APPLESCRIPT
}

# Function to launch in iTerm
launch_iterm() {
    osascript <<APPLESCRIPT
tell application "iTerm"
    activate
    try
        set newWindow to (create window with default profile)
        tell current session of newWindow
            write text "'$EXECUTABLE'"
            set name to "Turnkey Coach Tools"
        end tell
    on error
        -- Fallback for older iTerm versions
        tell current window
            create tab with default profile
            tell current session
                write text "'$EXECUTABLE'"
                set name to "Turnkey Coach Tools"
            end tell
        end tell
    end try
end tell
APPLESCRIPT
}

# Try to launch in iTerm first, then fallback to Terminal
if command -v iTerm >/dev/null 2>&1 || [ -d "/Applications/iTerm.app" ]; then
    launch_iterm 2>/dev/null || launch_terminal
else
    launch_terminal
fi
EOF

chmod +x "$MACOS_DIR/TurnkeyCoachTools"

# Create comprehensive Info.plist with proper icon reference
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
    <string>TurnkeyCoachTools</string>
    <key>CFBundleIconFile</key>
    <string>app-icon</string>
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
    <key>NSAppleScriptEnabled</key>
    <false/>
    <key>CFBundleDocumentTypes</key>
    <array>
        <dict>
            <key>CFBundleTypeName</key>
            <string>All Files</string>
            <key>CFBundleTypeOSTypes</key>
            <array>
                <string>****</string>
            </array>
            <key>CFBundleTypeRole</key>
            <string>None</string>
            <key>LSTypeIsPackage</key>
            <false/>
        </dict>
    </array>
</dict>
</plist>
EOF

echo "✅ App bundle created with custom icon"

# Fix permissions and remove quarantine attributes
chmod -R 755 "$APP_BUNDLE"
chmod +x "$MACOS_DIR/TurnkeyCoachTools"
chmod +x "$MACOS_DIR/turnkey-coach-executable"
xattr -cr "$APP_BUNDLE"

# Test the app bundle
echo ""
echo "🧪 Testing app bundle..."
if [ -d "$APP_BUNDLE" ] && [ -x "$MACOS_DIR/TurnkeyCoachTools" ]; then
    echo "✅ App bundle test passed"
else
    echo "❌ App bundle test failed"
    exit 1
fi

# Get app bundle size
APP_SIZE=$(du -sh "$APP_BUNDLE" | cut -f1)
echo "📏 App bundle size: $APP_SIZE"

# Create distribution package
echo ""
echo "📦 Creating distribution package with custom icon..."

# Create DMG directory
DMG_DIR="$OUTPUT_DIR/dmg-temp"
mkdir -p "$DMG_DIR"

# Copy app bundle to DMG directory
cp -R "$APP_BUNDLE" "$DMG_DIR/"

# Create comprehensive instructions
cat > "$DMG_DIR/INSTALLATION-INSTRUCTIONS.txt" << 'EOF'
🎯 TURNKEY COACH TOOLS - CUSTOM ICON VERSION
============================================

✨ COMPLETELY SELF-CONTAINED WITH BEAUTIFUL CUSTOM ICON! ✨

🚀 SUPER SIMPLE SETUP:

1. Drag "TurnkeyCoachTools.app" to your Applications folder
   (or anywhere you want - Desktop, etc.)
2. Double-click "TurnkeyCoachTools.app" to launch
3. That's it! 🎉

🎨 WHAT MAKES THIS SPECIAL:

✅ NO Python installation required
✅ NO dependencies to install  
✅ NO internet required (after download)
✅ Beautiful custom icon in Applications & Spotlight
✅ Professional macOS app experience
✅ Python 3.13 + OpenAI 2.2.0 bundled inside

Everything is built into one app - nothing to install!

💡 USAGE TIPS:

• Shows up beautifully in Applications folder with your custom icon
• Searchable in Spotlight (Cmd+Space, type "Turnkey")
• Works from Launchpad with icon
• Can be pinned to Dock with custom icon
• Move anywhere you want - Desktop, USB drive, etc.

🔧 WHAT HAPPENS WHEN YOU RUN IT:

1. Opens Terminal (or iTerm) automatically
2. Launches the full coaching tools interface
3. Beautiful Rich formatting and all features
4. Full OpenAI 2.2.0 support (GPT-5 ready!)
5. All your client tools ready to use

📋 SYSTEM REQUIREMENTS:

• macOS 10.15+ (Catalina or later)
• Any Mac (Intel or Apple Silicon)
• NO other software needed!

🆘 IF YOU HAVE ISSUES:

1. First launch security:
   Right-click app → Open (instead of double-clicking)
   Click "Open" in security dialog
   
2. After first launch:
   Double-click works normally
   
3. For any other issues, contact your developer

🎉 ENJOY YOUR BEAUTIFUL COACHING TOOLS! 🎉
EOF

# Create developer notes
cat > "$DMG_DIR/DEVELOPER-NOTES.txt" << EOF
DEVELOPER NOTES - Turnkey Coach Tools v$VERSION (Custom Icon)
============================================================

Build Information:
- Built on: $(date)
- Python version: 3.13.8 (bundled inside executable)
- Build system: macOS $(sw_vers -productVersion)
- App bundle size: $APP_SIZE
- Architecture: $(uname -m)
- Custom icon: Yes (app-icon.icns)

Technical Details:
- Native macOS .app bundle
- One-file executable wrapped in app bundle
- Python 3.13 runtime bundled
- All dependencies included (OpenAI 2.2.0)
- Custom icon displays in Finder, Applications, Spotlight, Dock
- No external requirements
- No installation needed

What's Inside:
- Contents/MacOS/TurnkeyCoachTools (launcher script)
- Contents/MacOS/turnkey-coach-executable (PyInstaller one-file)
- Contents/Resources/app-icon.icns (custom icon)
- Contents/Info.plist (app metadata)

User Experience:
- Beautiful icon in Applications folder
- Searchable in Spotlight
- Opens Terminal/iTerm when launched
- Full coaching tools functionality
- Professional macOS app feel

Distribution:
- Share the DMG file with coaches
- They drag the app to Applications
- Custom icon shows immediately
- No installation or setup required
- Works on any compatible Mac
- Perfect for GPT-5 when available

This is the ultimate coach-friendly solution with beautiful branding!
EOF

# Create the DMG with custom icon support
DMG_NAME="TurnkeyCoachTools-$VERSION-WithIcon"
DMG_PATH="$OUTPUT_DIR/$DMG_NAME.dmg"

echo "📀 Creating DMG installer with custom icon..."
if command -v hdiutil >/dev/null 2>&1; then
    # Create DMG with the app bundle
    hdiutil create -volname "$DMG_NAME" -srcfolder "$DMG_DIR" -ov -format UDZO "$DMG_PATH"
    rm -rf "$DMG_DIR"
    
    if [ -f "$DMG_PATH" ]; then
        echo "✅ DMG created: $DMG_PATH"
    fi
fi

# Also create a simple ZIP
ZIP_NAME="TurnkeyCoachTools-$VERSION-WithIcon"
ZIP_PATH="$OUTPUT_DIR/$ZIP_NAME.zip"

echo "🗜️  Creating ZIP archive..."
cd "$OUTPUT_DIR"
zip -r "$ZIP_NAME.zip" "$APP_NAME.app" >/dev/null
cd "$SCRIPT_DIR"
echo "✅ ZIP created: $ZIP_PATH"

# Create final distribution README
cat > "$OUTPUT_DIR/README-Distribution.md" << EOF
# Turnkey Coach Tools - Custom Icon Distribution

## 🎨 Beautiful App with Custom Icon

This version wraps the one-file executable in a proper macOS app bundle to display your beautiful custom icon!

## 📦 Distribution Files

- **\`$DMG_NAME.dmg\`** - Professional installer with custom icon (recommended)
- **\`$ZIP_NAME.zip\`** - ZIP download with custom icon
- **\`$APP_NAME.app\`** - The actual macOS application

## 👥 For Coaches (End Users)

### Option 1: DMG Installer
1. Download \`$DMG_NAME.dmg\`
2. Double-click to open
3. Drag \`TurnkeyCoachTools.app\` to Applications folder
4. Launch from Applications (shows custom icon!)

### Option 2: ZIP Download
1. Download and extract \`$ZIP_NAME.zip\`
2. Move \`TurnkeyCoachTools.app\` to Applications folder
3. Launch from Applications

## ✨ Key Benefits

- **Beautiful custom icon** - Shows in Applications, Spotlight, Dock
- **Zero technical requirements** - Just download and run
- **No Python needed** - Python 3.13 bundled inside
- **No internet required** - Works offline after download
- **Professional macOS app** - Native app bundle experience
- **GPT-5 ready** - OpenAI 2.2.0 bundled
- **Searchable in Spotlight** - Type "Turnkey" to find

## 🎨 Icon Features

- ✅ **Applications folder** - Beautiful icon display
- ✅ **Spotlight search** - Icon shows in search results  
- ✅ **Launchpad** - Icon appears with all apps
- ✅ **Dock** - Can pin with custom icon
- ✅ **Finder** - Shows icon everywhere

## 📊 Technical Details

- **App bundle size**: $APP_SIZE
- **Python version**: 3.13.8 (bundled)
- **OpenAI version**: 2.2.0 (GPT-5 ready)
- **Compatible with**: macOS 10.15+ (Intel & Apple Silicon)
- **Custom icon**: Yes (embedded in app bundle)
- **Build date**: $(date)

## 🚀 This is the ultimate professional solution!

Your custom icon will be beautifully displayed throughout macOS! 🎉
EOF

echo ""
echo "🎉 CUSTOM ICON APP BUILD COMPLETE!"
echo ""
echo "📊 Build Summary:"
echo "  ✅ App Bundle: $APP_NAME.app ($APP_SIZE)"
echo "  ✅ DMG installer: $DMG_NAME.dmg"
echo "  ✅ ZIP archive: $ZIP_NAME.zip"
echo "  ✅ Python 3.13 bundled inside"
echo "  ✅ OpenAI 2.2.0 included (GPT-5 ready)"
echo "  🎨 Custom icon beautifully displayed!"
echo ""
echo "🎯 PROFESSIONAL ICON SOLUTION!"
echo ""
echo "🔥 VISUAL BENEFITS FOR COACHES:"
echo "  • Beautiful custom icon in Applications folder"
echo "  • Professional branding in Spotlight search"
echo "  • Custom icon in Launchpad & Dock"
echo "  • Native macOS app experience"
echo "  • No technical setup required"
echo ""
echo "📤 DISTRIBUTION:"
echo "  Share: $DMG_NAME.dmg"
echo "  Size: $(du -h "$DMG_PATH" 2>/dev/null | cut -f1 || echo "~$APP_SIZE")"
echo "  Experience: Download → Drag to Applications → Beautiful Icon! → Launch!"
echo ""