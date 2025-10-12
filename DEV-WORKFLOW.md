# 🔧 Turnkey Coach Tools - Development Workflow

**Quick reference for Karl when adding features and rebuilding**

---

## 🚀 **Standard Development Flow**

### **1. Make Your Changes**
```bash
# Edit any Python files
vim coach_cli.py feed_tool.py upload_tool.py etc.

# Update dependencies if needed
vim requirements.txt
```

### **2. Test Locally**
```bash
# Quick test without building
python coach_cli.py

# OR test with simple launcher
./build-simple-launcher.sh
dist/simple-launcher/turnkey-coach
```

### **3. Build for Distribution**

#### **macOS:**
```bash
# Build one-file executable first (required)
./build-onefile.sh

# Then build app bundle with icon
./build-app-with-icon.sh
```

#### **Windows (GitHub Actions - Automated):**
```bash
# Push changes and create tag
git tag v1.4.0
git push origin v1.4.0
# Windows build happens automatically in GitHub Actions
```

#### **Windows (Manual - On Windows Machine):**
```powershell
# Run in PowerShell
.\build-windows.ps1 -Version "1.4.0"
```

### **4. Test the Built App**
```bash
# Test the app bundle
open dist/app-with-icon/TurnkeyCoachTools.app

# OR test the one-file directly
dist/onefile/turnkey-coach
```

---

## 📦 **What Gets Updated Automatically**

### ✅ **Python Code Changes**
- **All `.py` files** are bundled automatically
- **No rebuild config needed**
- **PyInstaller picks up all imports**

### ✅ **Dependencies (requirements.txt)**
- **Build script reinstalls** dependencies each time
- **PyInstaller bundles** new packages automatically
- **Version updates** handled automatically

### ✅ **Icon Changes**
- **Replace `app-icon.icns`** with new icon
- **Rebuild** - icon updates automatically

---

## 🔄 **Rebuild Scenarios**

### **After Code Changes:**
```bash
./build-onefile.sh && ./build-app-with-icon.sh
```

### **After Dependency Changes:**
```bash
# Same command - build script handles requirements.txt
./build-onefile.sh && ./build-app-with-icon.sh
```

### **Version Updates:**
```bash
# Update version in build scripts (search for "VERSION=")
# Then rebuild
./build-onefile.sh && ./build-app-with-icon.sh
```

---

## 📋 **Build Outputs**

### **macOS Distribution:**
- **`dist/app-with-icon/TurnkeyCoachTools-1.0.0-WithIcon.dmg`** ← Share this with Mac coaches
- **`dist/app-with-icon/TurnkeyCoachTools-1.0.0-WithIcon.zip`** ← Alternative download

### **Windows Distribution:**
- **`dist/windows/installer/TurnkeyCoachTools-1.0.0-Setup.exe`** ← Share this with Windows coaches  
- **`dist/windows/TurnkeyCoachTools-1.0.0-Windows.zip`** ← Standalone EXE

### **Development/Testing:**
- **`dist/onefile/turnkey-coach`** ← Single executable for testing (macOS)
- **`dist/simple-launcher/turnkey-coach`** ← Requires Python (for debugging)

---

## 🚀 **Release Process**

### **1. Update and Build**
```bash
# Make your changes
# Update version numbers if needed
./build-onefile.sh && ./build-app-with-icon.sh
```

### **2. Test Everything**
```bash
# Test the final DMG
open dist/app-with-icon/TurnkeyCoachTools-1.0.0-WithIcon.dmg
# Install and run the app
```

### **3. Commit Changes**
```bash
git add .  # Add your source changes only
git commit -m "Add new feature X"
git push origin develop
```

### **4. Create GitHub Release**
```bash
gh release create v1.4.0 --title "Version 1.4.0 - New Features" --notes "Description of changes"
gh release upload v1.4.0 dist/app-with-icon/TurnkeyCoachTools-1.0.0-WithIcon.dmg
gh release upload v1.4.0 dist/app-with-icon/TurnkeyCoachTools-1.0.0-WithIcon.zip
```

---

## 🐛 **Troubleshooting**

### **Build Fails:**
```bash
# Clean everything and retry
rm -rf dist/ build/ *.egg-info/
./build-onefile.sh && ./build-app-with-icon.sh
```

### **Missing Dependencies:**
```bash
# Check requirements.txt has all needed packages
pip freeze > temp-requirements.txt
# Compare with your requirements.txt
```

### **PyInstaller Issues:**
```bash
# Build with more verbose output
./build-onefile.sh  # Already has --debug-all flag
```

### **App Won't Launch:**
```bash
# Test the one-file executable directly
dist/onefile/turnkey-coach
# If it works, the issue is in app bundle wrapping
```

---

## 🎯 **Key Files to Remember**

### **Source Code:**
- **`coach_cli.py`** - Main entry point
- **`*_tool.py`** - Individual tools
- **`api_client.py`** - Server communication
- **`requirements.txt`** - Dependencies

### **Build System:**
- **`build-onefile.sh`** - Creates PyInstaller executable
- **`build-app-with-icon.sh`** - Wraps in macOS app bundle
- **`app-icon.icns`** - App icon
- **`BUILD-GUIDE.md`** - Complete build documentation

### **Distribution:**
- **`dist/app-with-icon/`** - Final coach-ready files
- **GitHub Releases** - Where coaches download

---

## 💡 **Development Tips**

### **Fast Iteration:**
```bash
# For quick testing during development
python coach_cli.py
# No build needed for source changes
```

### **Dependency Testing:**
```bash
# Test new dependencies before adding to requirements.txt
pip install new-package
python coach_cli.py  # Test it works
# Then add to requirements.txt
```

### **Icon Updates:**
```bash
# Replace app-icon.icns with new file
# Must be proper ICNS format
# Rebuild app bundle only:
./build-app-with-icon.sh
```

---

## 🔮 **Future: Apple Developer Account**

When you get access to Barbell Logic's Apple Developer account:

### **Add to build-app-with-icon.sh:**
```bash
# After app bundle creation, add:
codesign --force --options runtime --sign "Developer ID Application: Barbell Logic" "$APP_BUNDLE"
# Then notarize with Apple
```

**Everything else stays the same!** 

---

## 📝 **Quick Checklist for Releases**

- [ ] Code changes tested locally
- [ ] Requirements.txt updated if needed  
- [ ] Version numbers updated in build scripts
- [ ] Built and tested: `./build-onefile.sh && ./build-app-with-icon.sh`
- [ ] App launches and shows client list
- [ ] DMG created successfully
- [ ] Code committed to git
- [ ] GitHub release created
- [ ] DMG uploaded to release

**That's it! Your build system is solid.** 🎉