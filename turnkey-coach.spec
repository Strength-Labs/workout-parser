# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['coach_cli.py'],
    pathex=[],
    binaries=[],
    datas=[('requirements.txt', '.'), ('README.md', '.'), ('WARP.md', '.')],
    hiddenimports=['api_client', 'settings', 'directory_migration', 'encoding_utils', 'feed_tool', 'pr_tool', 'actual_prs_tool', 'format_tool', 'upload_tool', 'ai_chat_tool', 'rich.console', 'rich.panel', 'rich.table', 'rich.text', 'rich.prompt', 'rich.progress', 'requests', 'rapidfuzz', 'cryptography', 'openai', 'httpx'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='turnkey-coach',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app-icon.icns'],
)
