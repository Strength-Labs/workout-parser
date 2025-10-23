# 🎉 Turnkey Coach Tools - Installation Guide

**Download**: https://github.com/Strength-Labs/workout-parser/releases/tag/v1.3.0

---

## 🚨 Expected Security Warning

**Don't Panic!** macOS will show this warning:

> "TurnkeyCoachTools.app cannot be opened because Apple cannot verify that it is free from malware"

**This is normal!** The app is completely safe - it just isn't code-signed with an Apple certificate.

---

## ✅ **Method 1: Right-Click Method (Easiest)**

1. **Download** `TurnkeyCoachTools-1.4.0-WithIcon.dmg` from GitHub
2. **Open** the DMG file (double-click)
3. **Drag** the app to Applications folder
4. **Go to Applications** folder
5. **Right-click** on TurnkeyCoachTools.app
6. **Select "Open"** from the menu
7. **Click "Open"** in the security dialog
8. ✅ **App launches in Terminal** - you're ready!

---

## ✅ **Method 2: System Preferences Method**

If Method 1 doesn't work:

1. Try to open the app normally (it gets blocked)
2. **System Preferences** → **Security & Privacy** → **General**
3. You'll see a message about TurnkeyCoachTools being blocked
4. **Click "Open Anyway"**
5. **Confirm "Open"** in the dialog

---

## ✅ **Method 3: Terminal Fix (For Tech-Savvy Users)**

### Option A: Download the Fix Script
1. Download `fix-quarantine.sh` from the GitHub release
2. Open Terminal
3. Run: `bash ~/Downloads/fix-quarantine.sh`
4. Follow the prompts

### Option B: Manual Terminal Command
```bash
# Remove quarantine from the DMG file
xattr -d com.apple.quarantine ~/Downloads/TurnkeyCoachTools-1.4.0-WithIcon.dmg

# Then open normally
open ~/Downloads/TurnkeyCoachTools-1.4.0-WithIcon.dmg
```

---

## 🎯 **What Happens After Installation**

1. **Terminal Opens**: The app runs in Terminal (this is normal!)
2. **Client List**: You'll see your coaching clients
3. **Choose Tools**: Feed viewer, workout uploader, AI chat, etc.
4. **Ready to Coach**: Upload workouts, analyze PRs, chat with AI

---

## ⚙️ **System Requirements**

- **macOS 10.15+** (Catalina or newer)
- **Apple Silicon Mac** (M1/M2/M3/M4)
- **No Python needed** - everything is bundled!

*Note: Intel Macs are not supported in this build*

---

## ❓ **Troubleshooting**

### "App is damaged and can't be opened"
Try Method 3 (Terminal fix) to remove quarantine attributes.

### "No clients showing up"
1. Make sure you have internet connection
2. Check your Turnkey Coach login credentials
3. Contact Karl if issues persist

### "Command not found" in Terminal
The app bundle may be corrupted. Try:
1. Delete the app from Applications
2. Re-download the DMG
3. Use Method 3 to remove quarantine before installing

---

## 🔒 **Is This Safe?**

**Absolutely!** This app:
- ✅ Contains no malware or viruses  
- ✅ Only connects to Turnkey Coach servers
- ✅ Doesn't access your personal files
- ✅ Source code is available for inspection
- ✅ Built with standard Python tools

The warning only appears because the app isn't code-signed with Apple's $99/year developer certificate.

---

## 🆘 **Still Having Issues?**

**Contact Karl** with:
- Screenshot of any error messages
- Your macOS version (Apple Menu → About This Mac)  
- Which method you tried
- Whether you're on Intel or Apple Silicon

---

## 🚀 **Quick Start After Installation**

1. **Launch** the app (it opens in Terminal)
2. **Select your client** from the list
3. **Try the Feed Tool** first - it's the most popular!
4. **Upload workouts** using the Upload Tool
5. **Chat with AI** for programming help

---

**🎉 Happy Coaching!**

*No Python installation required - everything is bundled and ready to go!*