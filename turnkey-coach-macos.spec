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
    ('WARP.md', '.'),
]

# Add exerciselist.json if it exists
if os.path.exists('exerciselist.json'):
    datas.append(('exerciselist.json', '.'))

a = Analysis(
    ['coach_cli.py'],
    pathex=[spec_root],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # Core modules
        'api_client',
        'settings',
        'directory_migration',
        'encoding_utils',
        # Tool modules
        'feed_tool',
        'pr_tool',
        'actual_prs_tool',
        'format_tool',
        'upload_tool',
        'ai_chat_tool',
        'metrics_tool',
        # Workspace and sync modules (v1.5+)
        'workspace_manager',
        'workspace_setup',
        'bulk_sync',
        'display_utils',
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
    icon='app-icon.icns',  # Custom icon
)