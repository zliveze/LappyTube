# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Thu thập tất cả các module con của yt-dlp
yt_dlp_modules = collect_submodules('yt_dlp')

# Thu thập tất cả các file dữ liệu của yt-dlp
yt_dlp_data = collect_data_files('yt_dlp')

# Đường dẫn đến thư mục gốc của dự án
base_path = os.path.abspath('.')

# Đường dẫn đến thư mục assets
assets_path = os.path.join(base_path, 'assets')

# Danh sách các file cần thêm vào
added_files = [
    # Thêm thư mục assets
    (os.path.join(assets_path, 'bin'), 'assets/bin'),
    (os.path.join(assets_path, 'img'), 'assets/img'),
]

# Thêm các file dữ liệu của yt-dlp
added_files.extend(yt_dlp_data)

a = Analysis(
    ['src/main.py'],
    pathex=[base_path],
    binaries=[],
    datas=added_files,
    hiddenimports=yt_dlp_modules + ['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.sip'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LappyTube',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(assets_path, 'img', 'lappy.ico') if os.path.exists(os.path.join(assets_path, 'img', 'lappy.ico')) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LappyTube',
) 