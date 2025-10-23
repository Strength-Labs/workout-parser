# 🎉 Turnkey Coach Tools v1.5.0

## Highlights
- Multi-workspace support with per-workspace directories and encrypted credentials
- Windows first-run reliability: prompt for email/password, create directories, save token
- Smarter workout sync: detects deletions and fetches only new items
- Bulk Sync UX: clearer confirmation prompt
- Stability and safety: hardened token cache I/O and password input fallback

## Changes
- Workspace-aware paths: `~/Turnkey-{workspace}/clients`, `shared`, `coaching_context`
- Auto-migration helper for existing single-workspace installs
- Ensure shared dir exists before writing `.tokencache`
- getpass fallback to visible input when terminal cannot hide input (Windows shells)
- Exercise list loading robustness and type metadata retained

## Downloads
- macOS: TurnkeyCoachTools-1.5.0-WithIcon.dmg (and .zip)
- Windows: TurnkeyCoachTools-1.5.0-Setup.exe, TurnkeyCoachTools-1.5.0-Windows.zip

## Notes
- Unsigned builds; follow OS prompts (Right‑click → Open on macOS; “More info → Run anyway” on Windows).
