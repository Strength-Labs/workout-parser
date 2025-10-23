# Changelog

All notable changes to Turnkey Coach Tools will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.5.0] - 2025-10-17

### Added
- **Multi-workspace support** with per-workspace directories and encrypted credentials
- Workspace-aware paths: `~/Turnkey-{workspace}/clients`, `shared`, `coaching_context`
- Auto-migration helper for existing single-workspace installs
- Smarter workout sync that detects deletions and fetches only new items
- Bulk Sync UX with clearer confirmation prompts

### Fixed
- Windows first-run reliability: now prompts for email/password, creates directories, saves token
- Hardened token cache I/O for better stability
- Password input fallback to visible input when terminal cannot hide input (Windows shells)
- Exercise list loading robustness with type metadata retention
- Ensured shared directory exists before writing `.tokencache`

### Downloads
- macOS: `TurnkeyCoachTools-1.5.0-WithIcon.dmg`
- Windows: `TurnkeyCoachTools-1.5.0-Setup.exe`, `TurnkeyCoachTools-1.5.0-Windows.zip`

---

## [1.4.0] - 2025-10-12

### Added

#### Nutrition Calendar Support
- Full nutrition assignment support alongside workout programming
- Mix training (`Workout Date:`) and nutrition (`Nutrition Date:`) in same files
- Rich educational content with fun facts and check-in prompts

#### Enhanced Metrics System
- Track body composition (weight, body fat %, measurements)
- Performance metrics (RPE, recovery scores, sleep quality)
- Custom coach-defined metrics with intelligent fuzzy matching (70% similarity)
- Support for both prescribed targets and client tracking placeholders

#### Improved AI Chat
- Better context loading with date range filtering (3 months default)
- Token usage optimization to reduce costs
- Support for both OpenAI GPT and xAI Grok models
- Enhanced programming assistance and analysis

### Fixed
- Exercise parsing bug where nutrition content wasn't being saved
- Various stability improvements in markup parsing

### Technical
- Comprehensive markup language enhancements
- Robust metric name mapping with override support
- Enhanced upload validation with dry-run testing

### Downloads
- macOS: `TurnkeyCoachTools-1.4.0-WithIcon.dmg`
- Windows: `TurnkeyCoachTools-1.4.0-Setup.exe`, `TurnkeyCoachTools-1.4.0-Windows.zip`

---

## Installation Notes

### Security Warnings (All Versions)
Both macOS and Windows will show security warnings - **this is expected!** The apps are completely safe but aren't code-signed (we don't pay Apple/Microsoft's yearly certificate fees).

**macOS Workaround:**
- Right-click the app → "Open" → Click "Open" in security dialog
- OR: System Settings → Privacy & Security → "Open Anyway"

**Windows Workaround:**
- Click "More info" → "Run anyway"

### Requirements
- **macOS**: macOS 10.15+, Apple Silicon (M1/M2/M3/M4) or Intel
- **Windows**: Windows 10/11 (64-bit)
- **Linux**: Python 3.7+ (run from source)

---

## Previous Versions

Earlier version history can be found in `docs/project/changelog.md` (legacy format).

---

**Built for coaches, by coaches.** 💪
