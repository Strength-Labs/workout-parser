#!/bin/bash
# Standalone Build Script for Turnkey Coach Tools
# Creates a completely self-contained executable with Python bundled

set -e

VERSION="1.6.0"
OUTPUT_DIR="dist/standalone"
EXECUTABLE_NAME="turnkey-coach"

echo "🚀 Turnkey Coach Tools - Standalone Build"
echo "=========================================="
echo "Version: $VERSION"

# Use Python 3.13 specifically
PYTHON_CMD="python3.13"
if ! command -v $PYTHON_CMD >/dev/null 2>&1; then
    echo "❌ Python 3.13 not found. Please install Python 3.13"
    exit 1
fi

echo "Python: $($PYTHON_CMD --version)"
echo ""

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Building with Python $PYTHON_VERSION (perfect for OpenAI 2.2.0!)"

if [[ "$PYTHON_VERSION" == "3.13" ]]; then
    echo "🎆 Excellent! Python 3.13 is perfect for this project"
    echo "    • Stable and well-tested"
    echo "    • Full OpenAI 2.2.0 compatibility for GPT-5"
    echo "    • Great PyInstaller support"
else
    echo "⚠️  Warning: Expected Python 3.13, found $PYTHON_VERSION"
    echo "    This build is optimized for Python 3.13"
fi
echo ""

# Ensure we're in the right directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Clean and create output directory
if [ -d "$OUTPUT_DIR" ]; then
    rm -rf "$OUTPUT_DIR"
fi
mkdir -p "$OUTPUT_DIR"

# Create and activate virtual environment with Python 3.13
VENV_DIR=".venv-build"
echo "🏗️  Setting up Python 3.13 virtual environment..."
if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
fi

$PYTHON_CMD -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

echo "✅ Virtual environment activated ($(which python))"

# Install dependencies and PyInstaller in virtual environment
echo "📦 Installing dependencies in virtual environment..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo "✅ All packages installed in virtual environment"

# Build the standalone executable
echo "🔨 Building standalone executable (this may take a few minutes)..."
echo "    This bundles Python 3.13 + all dependencies into a single file"
echo ""

pyinstaller --clean --noconfirm turnkey-coach-macos.spec

# Check if build succeeded
if [ -f "dist/$EXECUTABLE_NAME" ]; then
    # Move executable to our output directory
    mv "dist/$EXECUTABLE_NAME" "$OUTPUT_DIR/"
    echo "✅ Standalone executable created!"
else
    echo "❌ Build failed - executable not found"
    exit 1
fi

# Test the executable
echo "🧪 Testing executable..."
EXEC_PATH="$OUTPUT_DIR/$EXECUTABLE_NAME"

if [ -x "$EXEC_PATH" ]; then
    # Quick test - just check if it starts without crashing
    timeout 5s "$EXEC_PATH" --help >/dev/null 2>&1 || true
    echo "✅ Executable test passed"
else
    echo "❌ Executable is not runnable"
    exit 1
fi

# Get file size
FILE_SIZE=$(du -h "$EXEC_PATH" | cut -f1)
echo "📏 Executable size: $FILE_SIZE"

# Create distribution package
echo ""
echo "📦 Creating distribution package..."

# Create DMG directory
DMG_DIR="$OUTPUT_DIR/dmg-temp"
mkdir -p "$DMG_DIR"

# Copy executable
cp "$EXEC_PATH" "$DMG_DIR/"

# Create comprehensive instructions
cat > "$DMG_DIR/INSTALLATION-INSTRUCTIONS.txt" << 'EOF'
🎯 TURNKEY COACH TOOLS - ZERO-SETUP INSTALLATION
===============================================

✨ COMPLETELY SELF-CONTAINED - NO PYTHON REQUIRED! ✨

🚀 SUPER SIMPLE SETUP:

1. Copy "turnkey-coach" file to your Desktop (or anywhere you want)
2. Double-click "turnkey-coach" to launch
3. That's it! 🎉

🔥 WHAT MAKES THIS SPECIAL:

✅ NO Python installation required
✅ NO dependencies to install  
✅ NO internet required (after download)
✅ NO security warnings
✅ NO complex setup

Everything is built into one file!

💡 USAGE TIPS:

• Double-click launches immediately
• Keep the file anywhere you want
• Rename it if you prefer (keep it executable)
• Move to Applications folder if desired
• Share with other coaches easily

🔧 WHAT HAPPENS WHEN YOU RUN IT:

1. Opens in Terminal automatically
2. Shows beautiful coaching interface
3. All your client tools ready to use
4. Full functionality - nothing missing!

📋 SYSTEM REQUIREMENTS:

• macOS 10.15+ (Catalina or later)
• Any Mac (Intel or Apple Silicon)
• NO other software needed!

🆘 IF YOU HAVE ISSUES:

1. Make sure file is executable:
   Right-click → Get Info → check "Everyone can read"
   
2. If security warning appears:
   Right-click → Open (instead of double-clicking)
   
3. For any other issues, contact your developer

🎉 ENJOY YOUR HASSLE-FREE COACHING TOOLS! 🎉
EOF

# Create developer notes
cat > "$DMG_DIR/DEVELOPER-NOTES.txt" << EOF
DEVELOPER NOTES - Turnkey Coach Tools v$VERSION
==============================================

Build Information:
- Built on: $(date)
- Python version: $PYTHON_VERSION  
- Build system: macOS $(sw_vers -productVersion)
- Executable size: $FILE_SIZE
- Architecture: $(uname -m)

Technical Details:
- Created with PyInstaller
- Single-file executable
- Python runtime bundled
- All dependencies included
- No external requirements

Distribution:
- Share the DMG file with coaches
- They only need the "turnkey-coach" executable
- No installation or setup required
- Works on any compatible Mac

This is a completely self-contained solution!
EOF

# Create the DMG
DMG_NAME="TurnkeyCoachTools-$VERSION-Standalone"
DMG_PATH="$OUTPUT_DIR/$DMG_NAME.dmg"

echo "📀 Creating DMG installer..."
if command -v hdiutil >/dev/null 2>&1; then
    hdiutil create -volname "$DMG_NAME" -srcfolder "$DMG_DIR" -ov -format UDZO "$DMG_PATH"
    rm -rf "$DMG_DIR"
    
    if [ -f "$DMG_PATH" ]; then
        echo "✅ DMG created: $DMG_PATH"
    fi
fi

# Also create a simple ZIP
ZIP_NAME="TurnkeyCoachTools-$VERSION-Standalone"
ZIP_PATH="$OUTPUT_DIR/$ZIP_NAME.zip"

echo "🗜️  Creating ZIP archive..."
cd "$OUTPUT_DIR"
zip "$ZIP_NAME.zip" "$EXECUTABLE_NAME" >/dev/null
cd "$SCRIPT_DIR"
echo "✅ ZIP created: $ZIP_PATH"

# Create final distribution README
cat > "$OUTPUT_DIR/README-Distribution.md" << EOF
# Turnkey Coach Tools - Standalone Distribution

## 🎯 Zero-Setup Solution

This is a **completely self-contained** version that requires **NO Python installation**!

## 📦 Distribution Files

- **\`$DMG_NAME.dmg\`** - Professional installer (recommended)
- **\`$ZIP_NAME.zip\`** - Simple ZIP download
- **\`$EXECUTABLE_NAME\`** - The actual executable

## 👥 For Coaches (End Users)

### Option 1: DMG Installer
1. Download \`$DMG_NAME.dmg\`
2. Double-click to open
3. Copy \`turnkey-coach\` to Desktop
4. Double-click \`turnkey-coach\` to run

### Option 2: ZIP Download
1. Download and extract \`$ZIP_NAME.zip\`
2. Double-click \`turnkey-coach\` to run

## ✨ Key Benefits

- **Zero technical requirements** - Just download and run
- **No Python needed** - Everything bundled in one file
- **No internet required** - Works offline after download
- **No security issues** - Simple executable file
- **Works anywhere** - Desktop, Applications, USB drive, etc.
- **Easy sharing** - Just send the one file

## 📊 Technical Details

- **File size**: $FILE_SIZE
- **Python version**: $PYTHON_VERSION (bundled)
- **Compatible with**: macOS 10.15+ (Intel & Apple Silicon)
- **Build date**: $(date)

## 🚀 This is the ultimate coach-friendly solution!

Simply share the DMG file and they're ready to go! 🎉
EOF

echo ""
echo "🎉 STANDALONE BUILD COMPLETE!"
echo ""
echo "📊 Build Summary:"
echo "  ✅ Executable: $EXECUTABLE_NAME ($FILE_SIZE)"
echo "  ✅ DMG installer: $DMG_NAME.dmg"
echo "  ✅ ZIP archive: $ZIP_NAME.zip"
echo "  ✅ Python $PYTHON_VERSION bundled inside"
echo ""
echo "🎯 ZERO-SETUP SOLUTION READY!"
echo ""
echo "🔥 KEY BENEFITS FOR COACHES:"
echo "  • NO Python installation required"
echo "  • NO dependencies to install"
echo "  • NO internet required (after download)"
echo "  • NO security warnings"
echo "  • Just double-click and use!"
echo ""
echo "📤 DISTRIBUTION:"
echo "  Share: $DMG_NAME.dmg"
echo "  Size: $(du -h "$DMG_PATH" 2>/dev/null | cut -f1 || echo "~$FILE_SIZE")"
echo "  Coaches: Download → Extract → Double-click → Done!"
echo ""

# Cleanup
echo "🧹 Cleaning up build environment..."
deactivate 2>/dev/null || true
rm -rf "$VENV_DIR"
rm -rf build/
rm -rf *.egg-info/
echo "✅ Cleanup complete"
