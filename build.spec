import platform

_WINDOWS = "Windows"
_LINUX = "Linux"
_MAC = "Darwin"

host_os = platform.system()

if host_os not in (_WINDOWS, _LINUX, _MAC):
    txt = f"""
    Unrecognized operating system: {host_os}
    """
    raise ValueError(txt)

# OS of the host, if its Darwin, Change it to MacOS
host_os = "MacOS (x86_64)" if platform.system() == _MAC else platform.system()

VERSION = "1.0"


print(f"""
Compiling Cubic Engine Game for {host_os}....
Pyinstaller config by @fkS124
""")


block_cipher = None


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src'), ('assets', 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

print("Finished importing the data folder")

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=f"Cubic Engine Game for {host_os}",
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

app = BUNDLE(exe,
         name=f"Cubic Engine Game",
         bundle_identifier=None)

print("The game has been successfully compiled.")