# Turnkey Coach Tools - Windows Build Script
# Creates standalone EXE and Inno Setup installer for Windows

param(
[string]$Version = "1.5.0"
)

Write-Host "🪟 Turnkey Coach Tools - Windows Build" -ForegroundColor Cyan
Write-Host "======================================"
Write-Host "Version: $Version"
Write-Host ""

# Check if we're on Windows
if ($IsLinux -or $IsMacOS) {
    Write-Host "❌ This script must run on Windows" -ForegroundColor Red
    exit 1
}

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Found: $pythonVersion"
} catch {
    Write-Host "❌ Python not found. Please install Python 3.13+" -ForegroundColor Red
    exit 1
}

# Create clean build environment
Write-Host "🧹 Cleaning build environment..."
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist\windows") { Remove-Item -Recurse -Force "dist\windows" }
New-Item -ItemType Directory -Force -Path "dist\windows" | Out-Null

# Create virtual environment for clean builds
Write-Host "🐍 Creating virtual environment..."
python -m venv .venv-windows
& ".venv-windows\Scripts\Activate.ps1"

# Install dependencies
Write-Host "📦 Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Build the executable
Write-Host "🔨 Building Windows executable..."
$iconParam = if (Test-Path "app-icon.ico") { "--icon=app-icon.ico" } else { "" }

pyinstaller --onefile --console --name "turnkey-coach" --hidden-import bulk_sync $iconParam --distpath "dist\windows" coach_cli.py

if (-not (Test-Path "dist\windows\turnkey-coach.exe")) {
    Write-Host "❌ Build failed - executable not found" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Executable created: dist\windows\turnkey-coach.exe"

# Get file size
$exeSize = (Get-Item "dist\windows\turnkey-coach.exe").Length
$sizeMB = [Math]::Round($exeSize / 1MB, 1)
Write-Host "📏 Executable size: $sizeMB MB"

# Create Inno Setup installer script
Write-Host "📄 Creating installer script..."

$innoScript = @"
#define MyAppName "Turnkey Coach Tools"
#define MyAppVersion "$Version"
#define MyAppPublisher "Barbell Logic"
#define MyAppURL "https://github.com/Strength-Labs/workout-parser"
#define MyAppExeName "turnkey-coach.exe"

[Setup]
AppId={{12345678-1234-5678-9ABC-DEF123456789}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist\windows\installer
OutputBaseFilename=TurnkeyCoachTools-$Version-Setup
$(if (Test-Path "app-icon.ico") { "SetupIconFile=app-icon.ico" })
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
Source: "dist\windows\turnkey-coach.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "COACH-INSTALL-GUIDE.md"; DestDir: "{app}"; Flags: ignoreversion; DestName: "Installation Guide.txt"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#SetupSetting('AppName')}}"; Flags: nowait postinstall skipifsilent

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nThis is a coaching tool for Barbell Logic's Turnkey Coach platform. No Python installation required - everything is bundled!
"@

New-Item -ItemType Directory -Force -Path "dist\windows\installer" | Out-Null
$innoScript | Out-File -FilePath "turnkey-coach-setup.iss" -Encoding UTF8

Write-Host "✅ Installer script created: turnkey-coach-setup.iss"

# Check for Inno Setup and build installer
$innoSetup = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (Test-Path $innoSetup) {
    Write-Host "🔧 Building installer with Inno Setup..."
    & $innoSetup "turnkey-coach-setup.iss"
    
    if (Test-Path "dist\windows\installer\TurnkeyCoachTools-$Version-Setup.exe") {
        $installerSize = [Math]::Round((Get-Item "dist\windows\installer\TurnkeyCoachTools-$Version-Setup.exe").Length / 1MB, 1)
        Write-Host "✅ Installer created: dist\windows\installer\TurnkeyCoachTools-$Version-Setup.exe ($installerSize MB)"
    } else {
        Write-Host "⚠️  Installer build may have failed" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Inno Setup not found - installer not created" -ForegroundColor Yellow
    Write-Host "   Download from: https://jrsoftware.org/isinfo.php" -ForegroundColor Cyan
}

# Create ZIP archive
Write-Host "🗜️  Creating ZIP archive..."
Compress-Archive -Path "dist\windows\turnkey-coach.exe" -DestinationPath "dist\windows\TurnkeyCoachTools-$Version-Windows.zip" -Force
Write-Host "✅ ZIP created: dist\windows\TurnkeyCoachTools-$Version-Windows.zip"

# Create distribution instructions
$instructions = @"
# Turnkey Coach Tools - Windows Distribution

## For Coaches (Choose One):

### 1. MSI Installer (Recommended)
**File:** `TurnkeyCoachTools-$Version-Setup.exe`
- Double-click to install
- Adds to Start Menu and Programs list  
- Creates desktop shortcut (optional)
- Professional installation experience

### 2. Standalone EXE (Advanced Users)
**File:** `TurnkeyCoachTools-$Version-Windows.zip`
- Extract and run turnkey-coach.exe
- No installation required
- Can run from USB drive

## System Requirements:
- Windows 10/11 (64-bit)
- No Python installation required
- All dependencies bundled

## Installation:
1. Download the installer (`TurnkeyCoachTools-$Version-Setup.exe`)
2. Run as Administrator if prompted
3. Follow installation wizard
4. Launch from Start Menu

## Usage:
- App opens in Command Prompt window
- Select your coaching clients  
- Use feed viewer, workout uploader, AI chat, etc.

## What's Bundled:
- Python 3.13 runtime
- OpenAI 2.2.0 (GPT-5 ready)
- Rich terminal formatting
- All dependencies included

**Built on:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Size:** ~$sizeMB MB (executable)
**No additional software required!**
"@

$instructions | Out-File -FilePath "dist\windows\README-Distribution.txt" -Encoding UTF8

# Deactivate virtual environment
deactivate 2>$null

Write-Host ""
Write-Host "🎉 WINDOWS BUILD COMPLETE!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Build Summary:" -ForegroundColor Cyan
Write-Host "  ✅ Executable: dist\windows\turnkey-coach.exe ($sizeMB MB)"
if (Test-Path "dist\windows\installer\TurnkeyCoachTools-$Version-Setup.exe") {
    $installerSize = [Math]::Round((Get-Item "dist\windows\installer\TurnkeyCoachTools-$Version-Setup.exe").Length / 1MB, 1)
    Write-Host "  ✅ Installer: dist\windows\installer\TurnkeyCoachTools-$Version-Setup.exe ($installerSize MB)"
}
Write-Host "  ✅ ZIP Archive: dist\windows\TurnkeyCoachTools-$Version-Windows.zip"
Write-Host "  ✅ All dependencies bundled (Python 3.13, OpenAI, Rich, etc.)"
Write-Host ""
Write-Host "📤 DISTRIBUTION:" -ForegroundColor Green
Write-Host "  Share: TurnkeyCoachTools-$Version-Setup.exe (installer)"
Write-Host "  Alt:   TurnkeyCoachTools-$Version-Windows.zip (standalone)"
Write-Host "  Experience: Download → Install → Start Menu → Launch!"