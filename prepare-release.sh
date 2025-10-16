#!/bin/bash
# Prepare v1.5.0 Release Script
# This script helps prepare the GitHub release

set -e

echo "🚀 Preparing Turnkey Coach Tools v1.5.0 Release"
echo "=============================================="

# Check if macOS build exists
if [ ! -f "dist/app-with-icon/TurnkeyCoachTools-1.5.0-WithIcon.dmg" ]; then
    echo "❌ macOS DMG not found. Run ./build-onefile.sh then ./build-app-with-icon.sh first"
    exit 1
fi

echo "✅ Found macOS DMG: dist/app-with-icon/TurnkeyCoachTools-1.5.0-WithIcon.dmg"

# Create release directory
mkdir -p release-files
cp "dist/app-with-icon/TurnkeyCoachTools-1.5.0-WithIcon.dmg" release-files/

# Create release notes file
cat > release-files/RELEASE_NOTES.md << 'EOF'
# 🎉 Turnkey Coach Tools v1.5.0

## ✨ Major New Features

### 🥗 **Nutrition Calendar Support**
- Full nutrition assignment support alongside workout programming
- Mix training (`Workout Date:`) and nutrition (`Nutrition Date:`) in same files
- Rich educational content with fun facts and check-in prompts

### 📊 **Enhanced Metrics System**
- Track body composition (weight, body fat %, measurements)
- Performance metrics (RPE, recovery scores, sleep quality)
- Custom coach-defined metrics with intelligent fuzzy matching (70% similarity)
- Support for both prescribed targets and client tracking placeholders

### 🤖 **Improved AI Chat**
- Better context loading with date range filtering (3 months default)
- Token usage optimization to reduce costs
- Support for both OpenAI GPT and xAI Grok models
- Enhanced programming assistance and analysis

### 🔧 **Technical Improvements**
- Fixed exercise parsing bug where nutrition content wasn't being saved
- Comprehensive markup language enhancements
- Robust metric name mapping with override support
- Enhanced upload validation with dry-run testing

## 📦 **Downloads**

### 🍎 **macOS** (Recommended)
- **TurnkeyCoachTools-1.5.0-WithIcon.dmg** - Beautiful app with custom icon
- Requires: macOS 10.15+, Apple Silicon (M1/M2/M3/M4)
- No Python installation needed - everything bundled!

### 🪟 **Windows**
- **TurnkeyCoachTools-1.5.0-Setup.exe** - Professional installer
- **TurnkeyCoachTools-1.5.0-Windows.zip** - Standalone executable
- Requires: Windows 10/11 (64-bit)
- No Python installation needed - everything bundled!

## ⚠️ **Security Warnings (Normal!)**
Both macOS and Windows will show security warnings - **this is expected!** The apps are completely safe but aren't code-signed. Follow the installation guides for easy workarounds.

## 📖 **Installation**
- **macOS**: See [Installation Guide](https://github.com/Strength-Labs/workout-parser/blob/develop/COACH-INSTALL-GUIDE.md)
- **Windows**: Download installer → Click "More info" → "Run anyway" → Follow wizard
- **Linux**: Install Python 3.7+ and run from source

## 🎯 **What's Next?**
This release focuses on comprehensive nutrition support and enhanced metrics tracking. Perfect for coaches managing both training and nutrition programs!

---
**Built for coaches, by coaches.** 💪
EOF

echo "✅ Created release notes: release-files/RELEASE_NOTES.md"

# Create instructions file
cat > release-files/INSTRUCTIONS.txt << 'EOF'
🚀 FINAL STEPS TO COMPLETE v1.5.0 RELEASE:

1. DOWNLOAD WINDOWS FILES:
   - Go to: https://github.com/Strength-Labs/workout-parser/actions
   - Click the latest "Build Windows Release" workflow
   - Download "windows-release" artifact (ZIP file)
   - Extract to get Windows files

2. CREATE GITHUB RELEASE:
   - Go to: https://github.com/Strength-Labs/workout-parser/releases
   - Click "Create a new release"
- Tag: v1.5.0
- Title: Turnkey Coach Tools v1.5.0
   - Copy-paste content from RELEASE_NOTES.md

3. UPLOAD FILES:
- TurnkeyCoachTools-1.5.0-WithIcon.dmg (already in this folder)
- TurnkeyCoachTools-1.5.0-Setup.exe (from GitHub Actions)
- TurnkeyCoachTools-1.5.0-Windows.zip (from GitHub Actions)

4. PUBLISH:
   - Check "Set as latest release"
   - Click "Publish release"

🎊 THEN GO TO THE WATERPARK! 🏊‍♂️
EOF

echo "✅ Created instructions: release-files/INSTRUCTIONS.txt"

# Show summary
echo ""
echo "📊 RELEASE SUMMARY:"
echo "  ✅ macOS DMG ready: $(du -h release-files/TurnkeyCoachTools-1.5.0-WithIcon.dmg | cut -f1)"
echo "  ✅ Release notes prepared"
echo "  ✅ Step-by-step instructions created"
echo ""
echo "📁 Everything is in: release-files/"
echo ""
echo "🎯 NEXT: Follow the simple instructions in release-files/INSTRUCTIONS.txt"
echo "   (Should take less than 5 minutes!)"
echo ""
echo "🏊‍♂️ The waterpark awaits!"
EOF