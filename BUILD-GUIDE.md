# Turnkey Coach Tools - Complete Build Guide

This document explains all the build scripts available and when to use each one.

## 🎯 Quick Reference - Which Script to Use?

| Goal | Script | Output | Best For |
|------|--------|---------|----------|
| **Final Distribution** | `./build-app-with-icon.sh` | App with beautiful icon | 🎨 **Ready for coaches** |
| Simple one-file | `./build-onefile.sh` | Single executable | Testing/development |
| Basic launcher | `./build-simple-launcher.sh` | Simple script | Debugging issues |
| Old app bundle | `./build-macos.sh` | App bundle (no icon) | Legacy/testing |
| Distribution prep | `./build-universal.sh` | Repackaged files | Documentation only |

## 🚀 RECOMMENDED: Final Production Build

### `./build-app-with-icon.sh` ⭐ **USE THIS FOR DISTRIBUTION**

**What it does:**
- Wraps the one-file executable in a proper macOS app bundle
- Embeds your custom icon beautifully
- Creates professional DMG and ZIP for distribution
- Works perfectly on M1/M2/M3/M4 Macs

**Requirements:**
- Must run `./build-onefile.sh` first (it uses that output)
- Needs `app-icon.icns` in project directory

**Output:**
```
dist/app-with-icon/
├── TurnkeyCoachTools.app                      # 🎨 App with your icon
├── TurnkeyCoachTools-1.0.0-WithIcon.dmg      # 📦 Share this with coaches
├── TurnkeyCoachTools-1.0.0-WithIcon.zip      # 📁 Alternative download
└── README-Distribution.md                     # 📖 Instructions
```

**When to use:**
- ✅ Final distribution to coaches
- ✅ When you want the beautiful custom icon
- ✅ Professional app bundle experience
- ✅ Ready-to-share DMG files

---

## 🔧 Development & Testing Builds

### `./build-onefile.sh` - One-File Executable

**What it does:**
- Creates single 23MB executable with Python 3.13 bundled
- Includes all dependencies (OpenAI 2.2.0, Rich, etc.)
- No Python installation required for users
- Attempts to embed icon (limited success for CLI apps)

**Requirements:**
- Python 3.13 installed
- All dependencies in `requirements.txt`

**Output:**
```
dist/onefile/
├── turnkey-coach                              # 🚀 Single executable file
├── TurnkeyCoachTools-1.0.0-OneFile.dmg
└── TurnkeyCoachTools-1.0.0-OneFile.zip
```

**When to use:**
- ✅ Creating the base for app bundle
- ✅ Testing the bundled executable
- ✅ Development/debugging

### `./build-simple-launcher.sh` - Simple Script

**What it does:**
- Creates simple shell script launcher
- Requires Python installation on target machine
- Installs dependencies on first run
- No app bundle, just executable script

**Output:**
```
dist/simple-launcher/
├── turnkey-coach                              # 📜 Shell script
├── TurnkeyCoachTools-1.0.0-Simple.dmg
└── (Python files copied alongside)
```

**When to use:**
- ✅ Debugging PyInstaller issues
- ✅ Quick testing
- ✅ When you need Python flexibility
- ❌ Not for distribution (requires Python)

---

## 🏗️ Legacy & Alternative Builds

### `./build-macos.sh` - Basic App Bundle

**What it does:**
- Creates macOS app bundle without proper icon support
- Opens Terminal when launched
- Requires Python on target machine

**When to use:**
- ✅ Testing app bundle structure
- ❌ Not recommended for distribution

### `./build-standalone.sh` - Broken Build

**Status:** ❌ **Currently broken** (spec file issues)
- Attempts PyInstaller with spec file
- Has path issues with data files
- Use `build-onefile.sh` instead

### `./build-universal.sh` - Distribution Helper

**What it does:**
- Repackages existing builds with better names
- Creates compatibility documentation
- Does NOT create universal binaries (misleading name)

**When to use:**
- ✅ Final packaging step
- ✅ Creating user documentation
- ❌ Does not solve Intel Mac compatibility

---

## 📋 Complete Build Process (Step by Step)

### For Final Distribution:

```bash
# 1. Ensure you have the icon
ls -la app-icon.icns  # Should exist and be ~700KB

# 2. Build the one-file executable first
./build-onefile.sh

# 3. Build the app bundle with icon (FINAL STEP)
./build-app-with-icon.sh

# 4. Optional: Package for distribution
./build-universal.sh

# 5. Share this file with coaches:
dist/app-with-icon/TurnkeyCoachTools-1.0.0-WithIcon.dmg
```

### For Development/Testing:

```bash
# Quick test build
./build-simple-launcher.sh
dist/simple-launcher/turnkey-coach

# Test bundled executable
./build-onefile.sh
dist/onefile/turnkey-coach
```

---

## 🎯 Architecture & Compatibility

### Current Builds Support:
- ✅ **Apple Silicon**: M1, M2, M3, M4, and future Macs
- ❌ **Intel Macs**: Not supported (would need separate build)

### To Add Intel Support:
You would need to:
1. Build on Intel Mac OR use GitHub Actions
2. Create both ARM64 and x86_64 executables  
3. Combine with `lipo -create` to make universal binary
4. Requires access to Intel Mac or CI/CD setup

### Market Coverage:
- **Current build**: ~95% of active Mac users (Apple Silicon)
- **Intel compatibility**: Would add ~5% (older Macs)

---

## 🔄 When to Rebuild

### Always rebuild when you change:
- ✅ Python source code (any `.py` files)
- ✅ Dependencies in `requirements.txt`
- ✅ Version numbers
- ✅ Icon file (`app-icon.icns`)

### Build order for changes:
1. Update source code
2. Test with `./build-simple-launcher.sh` (quick)
3. Build final with `./build-onefile.sh` then `./build-app-with-icon.sh`
4. Distribute the DMG from `dist/app-with-icon/`

---

## 🎨 Icon Requirements

### Your `app-icon.icns` file:
- ✅ Must be named exactly `app-icon.icns`
- ✅ Must be in project root directory
- ✅ Should be proper ICNS format with multiple resolutions
- ✅ Typical size: ~700KB (yours is perfect)

### If icon doesn't show:
- Check file exists: `ls -la app-icon.icns`
- Rebuild app bundle: `./build-app-with-icon.sh`
- Clear icon cache: `sudo rm -rf /Library/Caches/com.apple.iconservices.store`

---

## 🚨 Troubleshooting

### "One-file executable not found":
```bash
# Build the prerequisite first
./build-onefile.sh
# Then build app bundle
./build-app-with-icon.sh
```

### "Python 3.13 not found":
```bash
# Install Python 3.13
brew install python@3.13
# Or check if available
python3.13 --version
```

### "Custom icon not found":
```bash
# Check icon exists
ls -la app-icon.icns
# Icon must be in project root, named exactly "app-icon.icns"
```

### PyInstaller issues:
```bash
# Clean up and retry
rm -rf build/ dist/ *.egg-info/
./build-onefile.sh
```

---

## 📦 Final Distribution Checklist

Before sharing with coaches:

- [ ] ✅ `app-icon.icns` exists and displays properly
- [ ] ✅ Ran `./build-onefile.sh` successfully
- [ ] ✅ Ran `./build-app-with-icon.sh` successfully
- [ ] ✅ Tested the final app: `open dist/app-with-icon/TurnkeyCoachTools.app`
- [ ] ✅ App shows custom icon in Applications folder
- [ ] ✅ App launches and shows client list
- [ ] ✅ DMG file created: `dist/app-with-icon/TurnkeyCoachTools-1.0.0-WithIcon.dmg`

**Then share**: `TurnkeyCoachTools-1.0.0-WithIcon.dmg` 🎉

---

## 💡 Pro Tips

### Fastest development cycle:
```bash
# 1. Make code changes
# 2. Quick test:
./build-simple-launcher.sh && dist/simple-launcher/turnkey-coach
# 3. Final build when ready:
./build-onefile.sh && ./build-app-with-icon.sh
```

### Clean builds:
```bash
# Clean everything and start fresh
rm -rf dist/ build/ *.egg-info/ .venv-*
./build-onefile.sh
./build-app-with-icon.sh
```

### Version updates:
- Update version in all build scripts (search for "VERSION=")
- Rebuild both onefile and app-with-icon
- Test thoroughly before distribution

---

**📝 Last Updated:** $(date)  
**✅ Recommended Flow:** `build-onefile.sh` → `build-app-with-icon.sh` → Share DMG