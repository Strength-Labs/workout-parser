# 🚀 Cross-Platform Release - Quick Reference

**For Karl: The essential commands to release both macOS and Windows versions**

---

## 🎯 **Complete Release Process**

### **1. Development Complete → Build macOS**
```bash
git checkout develop
./build-onefile.sh && ./build-app-with-icon.sh
# Test the DMG works
```

### **2. Commit & Release**
```bash
git add . && git commit -m "Release v1.X.X - [Description]"
git checkout main && git merge develop && git push origin main
git checkout develop

gh release create v1.X.X \
  --title "Turnkey Coach Tools v1.X.X" \
  --notes "New features: [List]"

gh release upload v1.X.X \
  dist/app-with-icon/TurnkeyCoachTools-1.0.0-WithIcon.dmg \
  dist/app-with-icon/TurnkeyCoachTools-1.0.0-WithIcon.zip
```

### **3. Windows Build**
```bash
gh workflow run "Build Windows Release"

# Wait, then check status:
gh run list --workflow="build-windows.yml" --limit 1

# When ✓, download and upload:
gh run download [RUN_ID]
gh release upload v1.X.X \
  windows-release/windows-installer/TurnkeyCoachTools-1.0.0-Setup.exe \
  windows-release/TurnkeyCoachTools-1.0.0-Windows.zip
rm -rf windows-release
```

---

## ⚡ **Emergency Fixes**

### **Fix Build Issues:**
```bash
rm -rf dist/ build/ *.egg-info/
./build-onefile.sh && ./build-app-with-icon.sh
```

### **Windows Build Failed:**
```bash
# Check logs:
gh run view [RUN_ID] --log-failed
# Usually: filename issues or dependency problems
```

### **Wrong Version Numbers:**
```bash
# Search and replace in:
# - build-onefile.sh (VERSION=)
# - build-app-with-icon.sh (VERSION=)
# - .github/workflows/build-windows.yml (MyAppVersion)
```

---

## 📋 **File Checklist**

### **macOS Files to Upload:**
- `TurnkeyCoachTools-1.0.0-WithIcon.dmg` (main installer)
- `TurnkeyCoachTools-1.0.0-WithIcon.zip` (alternative)

### **Windows Files to Upload:**
- `TurnkeyCoachTools-1.0.0-Setup.exe` (main installer)
- `TurnkeyCoachTools-1.0.0-Windows.zip` (portable)

### **Support Files:**
- `COACH-INSTALL-GUIDE.md` (installation instructions)
- `fix-quarantine.sh` (macOS quarantine fix)

---

## 🔄 **Branch Management**

```bash
# Standard workflow:
git checkout develop          # Work here
# ... make changes ...
git checkout main            # Stable releases
git merge develop            # Bring in changes
git push origin main         # Deploy stable
git checkout develop         # Back to development
```

---

## 🎨 **Release Notes Template**

```markdown
# 🎉 Turnkey Coach Tools v1.X.X - [Title]

## New Features
- ✅ **[Feature]** - Description
- ✅ **[Feature]** - Description

## Download Options

### 🍎 **macOS (Apple Silicon)**
- **Recommended**: TurnkeyCoachTools-1.0.0-WithIcon.dmg
- **Alternative**: TurnkeyCoachTools-1.0.0-WithIcon.zip

### 🪟 **Windows (64-bit)**
- **Recommended**: TurnkeyCoachTools-1.0.0-Setup.exe  
- **Alternative**: TurnkeyCoachTools-1.0.0-Windows.zip

## Installation
[Standard installation instructions]

Cross-platform coaching tools - no technical setup required! 🏋️‍♂️
```

---

**🎯 Result:** Professional installers for both macOS and Windows coaches!