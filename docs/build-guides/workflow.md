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

## 🚀 **Complete Cross-Platform Release Process**

### **Step 1: Development & Testing**
```bash
# Work in develop branch
git checkout develop

# Make your changes
vim coach_cli.py feed_tool.py etc.

# Test locally
python coach_cli.py

# Quick test build (optional)
./build-simple-launcher.sh
```

### **Step 2: Build macOS Version**
```bash
# Build macOS executables
./build-onefile.sh && ./build-app-with-icon.sh

# Test the DMG
open dist/app-with-icon/TurnkeyCoachTools-1.0.0-WithIcon.dmg
# Install and verify it works
```

### **Step 3: Update Version Numbers** 
```bash
# Update version in build scripts if needed
# Search for "VERSION=" in:
# - build-onefile.sh
# - build-app-with-icon.sh  
# - build-windows.ps1
# - .github/workflows/build-windows.yml
```

### **Step 4: Commit & Merge to Main**
```bash
# Commit your changes
git add .  # Add source changes (NOT dist/ folder)
git commit -m "Add new feature X for v1.4.0"
git push origin develop

# Merge develop to main for stable release
git checkout main
git merge develop  
git push origin main
git checkout develop
```

### **Step 5: Create GitHub Release**
```bash
# Create the release
gh release create v1.4.0 --title "Turnkey Coach Tools v1.4.0" --notes "New features: X, Y, Z"

# Upload macOS files
gh release upload v1.4.0 dist/app-with-icon/TurnkeyCoachTools-1.0.0-WithIcon.dmg
gh release upload v1.4.0 dist/app-with-icon/TurnkeyCoachTools-1.0.0-WithIcon.zip
gh release upload v1.4.0 dist/onefile/TurnkeyCoachTools-1.0.0-OneFile.zip
```

### **Step 6: Trigger Windows Build**
```bash
# Windows build happens automatically via GitHub Actions
# Or trigger manually:
gh workflow run "Build Windows Release"

# Wait for build to complete (check with):
gh run list --workflow="build-windows.yml" --limit 1

# When complete (✓ status), download and upload:
gh run download [RUN_ID]  # Get RUN_ID from above command
gh release upload v1.4.0 windows-release/windows-installer/TurnkeyCoachTools-1.0.0-Setup.exe
gh release upload v1.4.0 windows-release/TurnkeyCoachTools-1.0.0-Windows.zip
rm -rf windows-release  # Clean up
```

### **Step 7: Update Release Notes**
```bash
# Create comprehensive release notes
cat > /tmp/release-notes.md << 'EOF'
# 🎉 Turnkey Coach Tools v1.4.0 - [Your Title]

## New Features
- ✅ **Feature 1** - Description
- ✅ **Feature 2** - Description  

## Download Options

### 🍎 **macOS (Apple Silicon)**
- **Recommended**: TurnkeyCoachTools-1.0.0-WithIcon.dmg
- **Alternative**: TurnkeyCoachTools-1.0.0-OneFile.zip

### 🪟 **Windows (64-bit)**  
- **Recommended**: TurnkeyCoachTools-1.0.0-Setup.exe
- **Alternative**: TurnkeyCoachTools-1.0.0-Windows.zip

[Include installation instructions, requirements, etc.]
EOF

# Update the release
gh release edit v1.4.0 --notes-file /tmp/release-notes.md
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

## 📝 **Quick Cross-Platform Release Checklist**

### **Pre-Release:**
- [ ] Code changes tested locally (`python coach_cli.py`)
- [ ] Requirements.txt updated if needed  
- [ ] Version numbers updated in build scripts (search "VERSION=")
- [ ] Built and tested macOS: `./build-onefile.sh && ./build-app-with-icon.sh`
- [ ] macOS app launches and shows client list
- [ ] Changes committed to develop branch
- [ ] Develop merged to main branch

### **Release Creation:**
- [ ] GitHub release created: `gh release create v1.X.X`
- [ ] macOS files uploaded (DMG, ZIP)
- [ ] Windows build triggered: `gh workflow run "Build Windows Release"`
- [ ] Windows build completed (✓ status)
- [ ] Windows files downloaded and uploaded
- [ ] Release notes updated with cross-platform instructions

### **Post-Release:**
- [ ] Both platform installers tested
- [ ] Release announcement ready for coaches
- [ ] Back to develop branch for next features

## 🚀 **One-Command Release (After Development)**

```bash
# The full release pipeline:
./build-onefile.sh && ./build-app-with-icon.sh  # Build macOS
git add . && git commit -m "Release v1.X.X"        # Commit
git checkout main && git merge develop && git push origin main && git checkout develop  # Merge
gh release create v1.X.X --title "Title" --notes "Notes"  # Create release
gh release upload v1.X.X dist/app-with-icon/*.dmg dist/app-with-icon/*.zip  # Upload macOS
gh workflow run "Build Windows Release"              # Trigger Windows build
# Then wait, download, and upload Windows files when ready
```

**Your cross-platform build system is ready!** 🎉
