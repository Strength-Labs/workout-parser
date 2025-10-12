#!/bin/bash

# Fix Quarantine Script for Turnkey Coach Tools
# This removes the macOS quarantine attribute that causes security warnings

echo "🔧 Turnkey Coach Tools - Quarantine Fix"
echo "======================================"
echo ""

# Find the downloaded DMG file
DMG_FILE=$(find ~/Downloads -name "TurnkeyCoachTools*.dmg" | head -1)

if [[ -z "$DMG_FILE" ]]; then
    echo "❌ No Turnkey Coach Tools DMG found in Downloads folder"
    echo ""
    echo "Please make sure you've downloaded the DMG from:"
    echo "https://github.com/Strength-Labs/workout-parser/releases"
    echo ""
    exit 1
fi

echo "✅ Found: $(basename "$DMG_FILE")"
echo ""

# Check if quarantine attribute exists
if xattr -l "$DMG_FILE" | grep -q "com.apple.quarantine"; then
    echo "🚨 Quarantine detected - removing it..."
    
    # Remove quarantine attribute
    xattr -d com.apple.quarantine "$DMG_FILE"
    
    if [[ $? -eq 0 ]]; then
        echo "✅ Quarantine removed successfully!"
        echo ""
        echo "🎉 You can now open the DMG file normally:"
        echo "   Double-click: $(basename "$DMG_FILE")"
        echo ""
        echo "   The app should install without security warnings."
    else
        echo "❌ Failed to remove quarantine attribute"
        echo "   Try running: sudo xattr -d com.apple.quarantine \"$DMG_FILE\""
    fi
else
    echo "✅ No quarantine found - file is already clean!"
    echo ""
    echo "🎉 You can open the DMG file normally:"
    echo "   Double-click: $(basename "$DMG_FILE")"
fi

echo ""
echo "📞 Need help? Contact Karl with any issues."