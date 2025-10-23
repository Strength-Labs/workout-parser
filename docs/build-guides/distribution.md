# Turnkey Coach Tools - Distribution Guide

This guide explains how to create one-click installers for both Windows and macOS platforms.

## Quick Start

### For macOS Users (building on macOS):
```bash
./build-macos.sh
```

### For Windows Users (building on Windows):
```powershell
.\build-windows.ps1
```

### Build Both (platform-specific):
```bash
./build-all.sh
```

## What Gets Created

### Windows Distribution (`dist/windows/`)
- **`TurnkeyCoachTools.exe`** - Standalone executable (no Python installation required)
- **`TurnkeyCoachTools.msi`** - Windows installer package with Start Menu shortcuts
- **`Launch-TurnkeyCoachTools.bat`** - Batch launcher with persistent window
- **`README-Windows.txt`** - Installation instructions for Windows users

### macOS Distribution (`dist/macos/`)
- **`TurnkeyCoachTools.app`** - macOS application bundle
- **`TurnkeyCoachTools-1.0.0.pkg`** - macOS installer package
- **`install-turnkey-coach.sh`** - Manual installation script
- **`README-macOS.txt`** - Installation instructions for macOS users

## How It Works

### Windows (PyInstaller + MSI)
1. **PyInstaller** bundles Python and all dependencies into a single `.exe`
2. **WiX Toolset** creates an MSI installer that:
   - Installs the exe to `%LOCALAPPDATA%\TurnkeyCoachTools\`
   - Creates Start Menu shortcuts
   - Creates desktop shortcuts
   - Handles uninstallation
3. Users double-click the MSI, install, then launch from Start Menu
4. The app opens in a new Command Prompt window

### macOS (App Bundle + PKG)
1. **App Bundle** structure contains Python scripts and launcher
2. **Launcher script** automatically:
   - Checks for Python 3.8+
   - Installs dependencies via pip
   - Opens Terminal with the CLI app
3. **PKG installer** installs the app bundle to `/Applications/`
4. Users double-click the PKG, install, then launch from Applications folder
5. The app opens in a new Terminal window

## User Experience

### Windows
1. Download `TurnkeyCoachTools.msi`
2. Double-click to run installer
3. Click through installation wizard
4. Launch from Start Menu: "Turnkey Coach Tools"
5. App opens in Command Prompt, ready to use

### macOS  
1. Download `TurnkeyCoachTools-1.0.0.pkg`
2. Double-click to run installer
3. Click through installation wizard
4. Launch from Applications folder or Launchpad
5. App opens in Terminal, ready to use

## Prerequisites for Building

### Windows Build Machine
- Windows 10 or later
- Python 3.8+
- PowerShell 5.0+
- WiX Toolset (auto-installed via winget if available)
- Internet connection

### macOS Build Machine  
- macOS 10.15 or later
- Python 3.8+
- Xcode Command Line Tools (for PKG creation)
- Internet connection

### Both Platforms
All Python dependencies from `requirements.txt` must be installable.

## Build Process Details

### Windows Build (`build-windows.ps1`)
1. Installs PyInstaller
2. Runs `pyinstaller turnkey-coach.spec` to create standalone EXE
3. Generates WiX installer source (`.wxs` file)
4. Compiles MSI using WiX Toolset
5. Creates batch launcher and documentation

### macOS Build (`build-macos.sh`)
1. Creates app bundle directory structure
2. Copies Python files to `Resources/`
3. Creates launcher script that opens Terminal
4. Generates PKG installer using `pkgbuild`
5. Creates manual installer script and documentation

## Testing

### Before Distribution
1. **Test on clean systems** without Python or dependencies
2. **Test first-run experience** - dependency installation
3. **Test app functionality** - ensure all features work
4. **Test uninstallation** (Windows MSI uninstaller)

### Windows Testing
```powershell
# Test the executable directly
.\dist\windows\TurnkeyCoachTools.exe

# Test the MSI installer
msiexec /i dist\windows\TurnkeyCoachTools.msi
```

### macOS Testing
```bash
# Test the app bundle directly
open dist/macos/TurnkeyCoachTools.app

# Test the PKG installer  
open dist/macos/TurnkeyCoachTools-1.0.0.pkg
```

## Distribution

### File Sharing
- **Windows**: Share the entire `dist/windows/` folder
- **macOS**: Share the entire `dist/macos/` folder
- **Cross-platform**: Share both folders with clear platform labels

### File Hosting
Upload to file hosting service with clear instructions:
```
TurnkeyCoachTools-v1.0.0/
├── Windows/
│   ├── TurnkeyCoachTools.msi          # ← Windows users download this
│   ├── TurnkeyCoachTools.exe          # Alternative: portable exe
│   └── README-Windows.txt
└── macOS/
    ├── TurnkeyCoachTools-1.0.0.pkg    # ← macOS users download this  
    ├── TurnkeyCoachTools.app           # Alternative: manual install
    └── README-macOS.txt
```

## Troubleshooting

### Windows Build Issues
- **"PyInstaller not found"**: Run `pip install pyinstaller`
- **"WiX not found"**: Install manually from https://wixtoolset.org/
- **Import errors**: Check `turnkey-coach.spec` hiddenimports list

### macOS Build Issues  
- **"pkgbuild not found"**: Install Xcode Command Line Tools
- **Permission denied**: Ensure `build-macos.sh` is executable
- **Python version errors**: Ensure Python 3.8+ is available

### Runtime Issues
- **Windows**: Check Windows Event Viewer for application errors
- **macOS**: Check Console app for error messages
- **Both**: Test with `python coach_cli.py` directly first

## Advanced Options

### Code Signing (Optional)
For public distribution, consider signing the installers:

**Windows**: Use `signtool.exe` with a code signing certificate
**macOS**: Use `codesign` with Apple Developer Certificate

### Custom Icons
Add application icons by:
1. Creating icon files (`.ico` for Windows, `.icns` for macOS)
2. Adding to PyInstaller spec or app bundle
3. Updating installer configurations

### Version Updates
Update version numbers in:
- `setup.py`
- `build-windows.ps1` (Version parameter)
- `build-macos.sh` (VERSION variable)
- App bundle Info.plist

## Support

For build issues or questions about the distribution process, contact the developer.