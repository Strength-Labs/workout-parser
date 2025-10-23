# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Turnkey Coach Tools - macOS Standalone

import sys
import os
from pathlib import Path

block_cipher = None

# Get the directory containing this spec file
spec_root = os.path.dirname(os.path.abspath(SPEC))

# Build datas list properly, filtering out None values
datas = [
    ('requirements.txt', '.'),
    ('README.md', '.'),
    ('docs/project/warp.md', '.'),
]

# Add exerciselist.json if it exists
if os.path.exists('exerciselist.json'):
    datas.append(('exerciselist.json', '.'))

a = Analysis(
    ['src/coach_cli.py'],
    pathex=[spec_root],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # Core package
        'src',
        # Core modules
        'src.api_client',
        'src.settings',
        'src.directory_migration',
        'src.encoding_utils',
        # Tool modules
        'src.tools.feed_tool',
        'src.tools.pr_tool',
        'src.tools.actual_prs_tool',
        'src.tools.format_tool',
        'src.tools.upload_tool',
        'src.tools.ai_chat_tool',
        'src.tools.metrics_tool',
        # Workspace and sync modules (v1.5+)
        'src.workspace_manager',
        'src.workspace_setup',
        'src.bulk_sync',
        'src.display_utils',
        # Rich components
        'rich.console',
        'rich.panel',
        'rich.table',
        'rich.text',
        'rich.prompt',
        'rich.progress',
        'rich.markup',
        'rich.align',
        'rich.columns',
        'rich.live',
        'rich.spinner',
        'rich.status',
        # Core dependencies
        'requests',
        'rapidfuzz',
        'cryptography',
        'openai',
        'httpx',
        # Python standard library modules that might be missed
        'json',
        'datetime',
        'pathlib',
        'subprocess',
        'getpass',
        'tempfile',
        'base64',
        'urllib',
        'urllib.parse',
        'urllib.request',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Datas are already properly built above

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='turnkey-coach',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Console app for terminal interaction
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/app-icon.icns',  # Custom icon
)