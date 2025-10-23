# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/coach_cli.py'],
    pathex=[],
    binaries=[],
    datas=[('requirements.txt', '.'), ('README.md', '.'), ('docs/project/warp.md', '.')],
    hiddenimports=['src', 'src.api_client', 'src.settings', 'src.directory_migration', 'src.encoding_utils', 'src.tools.feed_tool', 'src.tools.pr_tool', 'src.tools.actual_prs_tool', 'src.tools.format_tool', 'src.tools.upload_tool', 'src.tools.ai_chat_tool', 'src.bulk_sync', 'src.display_utils', 'src.workspace_manager', 'src.workspace_setup', 'src.tools.metrics_tool', 'rich.console', 'rich.panel', 'rich.table', 'rich.text', 'rich.prompt', 'rich.progress', 'rich.live', 'requests', 'rapidfuzz', 'cryptography', 'openai', 'httpx'],
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
    icon=['assets/app-icon.icns'],
)
