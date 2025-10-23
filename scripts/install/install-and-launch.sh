#!/bin/bash
# Turnkey Coach Tools - Auto Installer with Security Bypass
# This script handles installation and first launch automatically

set -e

echo "🎯 Turnkey Coach Tools - Smart Installer"
echo "=========================================="
echo ""

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_BUNDLE="$SCRIPT_DIR/TurnkeyCoachTools.app"

# Check if app bundle exists
if [ ! -d "$APP_BUNDLE" ]; then
    echo "❌ Error: TurnkeyCoachTools.app not found!"
    echo "   Make sure this script is in the same folder as the app."
    exit 1
fi

echo "📦 Installing Turnkey Coach Tools to Applications..."

# Remove existing installation
if [ -d "/Applications/TurnkeyCoachTools.app" ]; then
    echo "   Removing existing installation..."
    rm -rf "/Applications/TurnkeyCoachTools.app"
fi

# Copy to Applications
cp -R "$APP_BUNDLE" "/Applications/"

# Fix permissions and remove quarantine
echo "🔧 Fixing permissions and security attributes..."
chmod -R 755 "/Applications/TurnkeyCoachTools.app"
chmod +x "/Applications/TurnkeyCoachTools.app/Contents/MacOS/turnkey-coach"
xattr -cr "/Applications/TurnkeyCoachTools.app"

echo "✅ Installation complete!"
echo ""

# Offer to launch the app
echo "🚀 Would you like to launch Turnkey Coach Tools now? (y/n)"
read -r launch_choice

if [[ "$launch_choice" =~ ^[Yy]$ ]]; then
    echo "   Launching application..."
    echo "   Note: This will open in iTerm or Terminal"
    echo ""
    
    # Launch the app
    open "/Applications/TurnkeyCoachTools.app"
    
    echo "✅ Application launched!"
    echo ""
    echo "💡 Future launches:"
    echo "   • Use Spotlight: Cmd+Space, type 'Turnkey'"
    echo "   • Or go to Applications folder and double-click"
else
    echo ""
    echo "📍 To launch later:"
    echo "   • Use Spotlight: Cmd+Space, type 'Turnkey'"
    echo "   • Or go to Applications → TurnkeyCoachTools"
fi

echo ""
echo "🎉 Setup complete! Enjoy using Turnkey Coach Tools!"
echo ""