# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['oss_main.py'],
    pathex=['D:\\BP TECH\\Python apps\\REPOs\\AutomationSuite\\Core'],
    binaries=[],
    datas=[('One_BP_IQ fixed.01.xlsx', '.'), ('workflows.json', '.'), ('service_label_mapping.json', '.'), ('oss_config.yaml', '.')],
    hiddenimports=['customtkinter', 'ttkthemes', 'pandas', 'openpyxl', 'tkinter', 'tkinter.ttk', 'Core.rate_calculations', 'Core.workflow_manager', 'Core.language_pair_manager', 'Core.service_mapping_manager'],
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
    name='OneStopShop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
