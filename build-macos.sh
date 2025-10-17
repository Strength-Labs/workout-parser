#!/bin/bash
# Build Script for macOS Installer
# This script creates a macOS app bundle and PKG installer for Turnkey Coach Tools

set -e

VERSION="1.5.0"
OUTPUT_DIR="dist/macos"
APP_NAME="TurnkeyCoachTools"
BUNDLE_ID="com.karlschudt.turnkey-coach-tools"

echo "=== Turnkey Coach Tools - macOS Build Script ==="
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

echo "Creating app bundle structure..."

# Copy Info.plist (already created)
if [ ! -f "$CONTENTS_DIR/Info.plist" ]; then
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
</dict>
</plist>
EOF
fi

# Copy main executable wrapper (already created)
if [ ! -f "$MACOS_DIR/turnkey-coach" ]; then
    cat > "$MACOS_DIR/turnkey-coach" << 'EOF'
#!/bin/bash
# Turnkey Coach Tools - macOS App Bundle Launcher

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
RESOURCES_DIR="$APP_DIR/Contents/Resources"

# Set up environment
export PYTHONPATH="$RESOURCES_DIR:$PYTHONPATH"

# Change to the resources directory where our Python files are
cd "$RESOURCES_DIR"

# Check if Python 3 is installed
if ! command -v python3 >/dev/null 2>&1; then
    osascript -e 'display dialog "Python 3 is required but not installed. Please install Python 3.8 or later from python.org" with title "Turnkey Coach Tools" buttons {"OK"} default button 1 with icon stop'
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
REQUIRED_VERSION="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" 2>/dev/null; then
    osascript -e "display dialog \"Python $PYTHON_VERSION found, but Python $REQUIRED_VERSION or later is required.\" with title \"Turnkey Coach Tools\" buttons {\"OK\"} default button 1 with icon stop"
    exit 1
fi

# Install dependencies if needed
if [ ! -f "$RESOURCES_DIR/.deps_installed" ]; then
    osascript -e 'display dialog "Installing dependencies... This may take a moment." with title "Turnkey Coach Tools" buttons {"OK"} default button 1 with icon note giving up after 3'
    
    if pip3 install -r "$RESOURCES_DIR/requirements.txt" --user --quiet; then
        touch "$RESOURCES_DIR/.deps_installed"
    else
        osascript -e 'display dialog "Failed to install dependencies. Please check your internet connection and try again." with title "Turnkey Coach Tools" buttons {"OK"} default button 1 with icon stop'
        exit 1
    fi
fi

# Open Terminal with our application
osascript <<APPLESCRIPT
tell application "Terminal"
    activate
    set newTab to do script "cd '$RESOURCES_DIR' && python3 coach_cli.py"
    set custom title of newTab to "Turnkey Coach Tools"
end tell
APPLESCRIPT
EOF
    chmod +x "$MACOS_DIR/turnkey-coach"
fi

# Copy Python application files to Resources
# Copy app icon if it exists
if [ -f "app-icon.icns" ]; then
    cp "app-icon.icns" "$RESOURCES_DIR/"
    echo "  Copied: app-icon.icns"
fi

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
        echo "  Copied: $file"
    else
        echo "  Warning: $file not found"
    fi
done

echo "✓ App bundle created: $APP_BUNDLE"

# Create a simple installer script
echo "Creating installer script..."
INSTALLER_SCRIPT="$OUTPUT_DIR/install-turnkey-coach.sh"
cat > "$INSTALLER_SCRIPT" << 'EOF'
#!/bin/bash
# Turnkey Coach Tools - macOS Installer

echo "=== Turnkey Coach Tools - macOS Installer ==="
echo ""

# Check if running with proper permissions
if [[ $EUID -eq 0 ]]; then
    echo "This installer should not be run as root."
    exit 1
fi

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_BUNDLE="$SCRIPT_DIR/TurnkeyCoachTools.app"

if [ ! -d "$APP_BUNDLE" ]; then
    echo "Error: TurnkeyCoachTools.app not found in $SCRIPT_DIR"
    exit 1
fi

# Install to Applications folder
APPLICATIONS_DIR="/Applications"
INSTALL_PATH="$APPLICATIONS_DIR/TurnkeyCoachTools.app"

echo "Installing Turnkey Coach Tools..."

# Remove existing installation
if [ -d "$INSTALL_PATH" ]; then
    echo "Removing existing installation..."
    rm -rf "$INSTALL_PATH"
fi

# Copy app bundle
echo "Copying application to $APPLICATIONS_DIR..."
cp -R "$APP_BUNDLE" "$APPLICATIONS_DIR/"

# Set proper permissions
chmod -R 755 "$INSTALL_PATH"
chmod +x "$INSTALL_PATH/Contents/MacOS/turnkey-coach"

echo ""
echo "✓ Installation complete!"
echo ""
echo "You can now launch Turnkey Coach Tools from:"
echo "  • Applications folder"
echo "  • Launchpad"
echo "  • Spotlight (search for 'Turnkey Coach')"
echo ""
echo "The application will open in Terminal when launched."
echo ""
read -p "Press Enter to exit..."
EOF

chmod +x "$INSTALLER_SCRIPT"

# Create a PKG installer using pkgbuild (requires developer tools)
echo "Creating PKG installer..."
PKG_PATH="$OUTPUT_DIR/TurnkeyCoachTools-$VERSION.pkg"

if command -v pkgbuild >/dev/null 2>&1; then
    # Create temporary directory for package root
    PKG_ROOT=$(mktemp -d)
    PKG_APPS_DIR="$PKG_ROOT"
    mkdir -p "$PKG_APPS_DIR"
    
    # Copy app bundle to package root (this will be the /Applications directory)
    cp -R "$APP_BUNDLE" "$PKG_APPS_DIR/"
    
    # Create the package with correct install location
    pkgbuild --root "$PKG_ROOT" \
             --identifier "$BUNDLE_ID" \
             --version "$VERSION" \
             --install-location "/Applications" \
             "$PKG_PATH"
    
    # Clean up
    rm -rf "$PKG_ROOT"
    
    if [ -f "$PKG_PATH" ]; then
        echo "✓ PKG installer created: $PKG_PATH"
    else
        echo "Failed to create PKG installer"
    fi
else
    echo "pkgbuild not found. Skipping PKG creation."
    echo "To create PKG installers, install Xcode Command Line Tools:"
    echo "  xcode-select --install"
fi

# Create distribution README
cat > "$OUTPUT_DIR/README-macOS.txt" << 'EOF'
# Turnkey Coach Tools - macOS Distribution

## Installation Options

### Option 1: PKG Installer (Recommended)
1. Double-click `TurnkeyCoachTools-1.0.0.pkg`
2. Follow the installation wizard
3. Launch from Applications folder or Launchpad

### Option 2: Manual Installation
1. Run `install-turnkey-coach.sh`
2. Follow the prompts
3. Launch from Applications folder

### Option 3: Run Directly
1. Double-click `TurnkeyCoachTools.app`
2. The app will open in Terminal

## What's Included

- `TurnkeyCoachTools.app` - macOS application bundle
- `TurnkeyCoachTools-1.0.0.pkg` - macOS installer package (if available)
- `install-turnkey-coach.sh` - Manual installation script
- This README file

## System Requirements

- macOS 10.15 (Catalina) or later
- Python 3.8 or later (will be installed automatically if missing)
- Internet connection for API access and dependency installation

## First Launch

When you first launch the application:
1. It will open Terminal automatically
2. Dependencies will be installed if needed
3. The CLI interface will start

## Data Storage

The application creates a data directory at:
`~/Turnkey/`

Your workout data, settings, and cached files are stored there.

## Troubleshooting

If the app doesn't launch:
1. Make sure Python 3.8+ is installed
2. Run the app from Terminal to see error messages
3. Check that all dependencies are installed

## Support

For issues or questions, please contact the developer.
EOF

echo ""
echo "=== Build Complete ==="
echo "Output directory: $OUTPUT_DIR"
echo "✓ App Bundle: $APP_NAME.app"
if [ -f "$PKG_PATH" ]; then
    echo "✓ PKG Installer: TurnkeyCoachTools-$VERSION.pkg"
fi
echo "✓ Manual Installer: install-turnkey-coach.sh"
echo "✓ Documentation: README-macOS.txt"
echo ""
echo "To test the app bundle:"
echo "  open '$APP_BUNDLE'"
echo ""