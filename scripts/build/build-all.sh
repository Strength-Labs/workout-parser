#!/bin/bash
# Master Build Script for Turnkey Coach Tools
# Builds installers for both Windows and macOS platforms

set -e

VERSION="1.6.0"
PROJECT_NAME="TurnkeyCoachTools"

echo "=== Turnkey Coach Tools - Master Build Script ==="
echo "Version: $VERSION"
echo ""

# Ensure we're in the right directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/
mkdir -p dist

# Check if we're on macOS or Windows/WSL
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Building on macOS..."
    
    # Build macOS version
    echo ""
    echo "=== Building macOS Installer ==="
    ./build-macos.sh
    
    echo ""
    echo "=== macOS Build Complete ==="
    echo "To test the macOS app:"
    echo "  open 'dist/macos/TurnkeyCoachTools.app'"
    
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    echo "Building on Windows..."
    
    # Build Windows version using PowerShell
    echo ""
    echo "=== Building Windows Installer ==="
    powershell.exe -ExecutionPolicy Bypass -File "./build-windows.ps1"
    
    echo ""
    echo "=== Windows Build Complete ==="
    echo "Windows installer available at: dist/windows/TurnkeyCoachTools.msi"
    
else
    echo "Unsupported operating system: $OSTYPE"
    echo "This script supports macOS and Windows."
    exit 1
fi

# Create distribution info
DIST_INFO="dist/BUILD-INFO.txt"
cat > "$DIST_INFO" << EOF
# Turnkey Coach Tools - Build Information

Build Date: $(date)
Version: $VERSION
Platform: $OSTYPE
Built by: $(whoami)

## Files Generated

This build process creates platform-specific installers:

### Windows (when built on Windows):
- dist/windows/TurnkeyCoachTools.exe - Standalone executable
- dist/windows/TurnkeyCoachTools.msi - Windows installer package
- dist/windows/Launch-TurnkeyCoachTools.bat - Batch launcher
- dist/windows/README-Windows.txt - Windows installation guide

### macOS (when built on macOS):
- dist/macos/TurnkeyCoachTools.app - macOS application bundle
- dist/macos/TurnkeyCoachTools-$VERSION.pkg - macOS installer package
- dist/macos/install-turnkey-coach.sh - Manual installation script
- dist/macos/README-macOS.txt - macOS installation guide

## Distribution

1. For Windows users: Provide the entire dist/windows/ folder
2. For macOS users: Provide the entire dist/macos/ folder
3. Users can choose between MSI/PKG installers or manual installation

## Testing

Before distributing:
1. Test on clean Windows 10+ system (Windows version)
2. Test on clean macOS 10.15+ system (macOS version)
3. Verify all dependencies are bundled correctly
4. Test first-time user experience

EOF

echo ""
echo "=== Master Build Complete ==="
echo ""
echo "Distribution files created:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  macOS: dist/macos/"
    ls -la dist/macos/
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    echo "  Windows: dist/windows/"
    ls -la dist/windows/
fi
echo ""
echo "Build information: $DIST_INFO"
echo ""
echo "Next steps:"
echo "1. Test the installers on clean systems"
echo "2. Sign the installers if distributing publicly"
echo "3. Create distribution packages"
echo ""