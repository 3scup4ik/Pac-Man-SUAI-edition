# -*- mode: python ; coding: utf-8 -*-

datas = [
    ('assets/sounds/Pac Man Chomp.wav', 'assets/sounds'),
    ('assets/sounds/death.mp3', 'assets/sounds'),
    ('assets/sounds/win.mp3', 'assets/sounds'),
    ('assets/sounds/pac-man-ghost-eat.mp3', 'assets/sounds'),
    ('assets/sounds/Power Up.mp3', 'assets/sounds'),
]

a = Analysis(
    ['pac-man.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='pac-man',
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
    icon='pac-man.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='pac-man',
)
