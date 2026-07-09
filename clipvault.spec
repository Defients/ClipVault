# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for building ClipVault into a standalone .exe."""

import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Collect all submodules for packages that use dynamic imports
hiddenimports = []
hiddenimports += collect_submodules('pynput')
hiddenimports += [
    'pyperclip',
    'cryptography',
    'cryptography.fernet',
    'cryptography.hazmat.primitives.kdf.pbkdf2',
    'cryptography.hazmat.primitives.hashes',
    'cryptography.hazmat.backends',
]
# Optional dependencies – included if available
for opt in ('PIL', 'pytesseract', 'rapidfuzz'):
    try:
        __import__(opt)
        hiddenimports += collect_submodules(opt)
    except ImportError:
        pass

a = Analysis(
    ['clipvault/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/CLIPVAULT.ico', 'assets')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'pytest_cov', 'tests'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ClipVault',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/CLIPVAULT.ico',
)
