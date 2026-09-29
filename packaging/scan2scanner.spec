# -*- mode: python ; coding: utf-8 -*-

import platform
from pathlib import Path


project_root = Path(SPECPATH).parent
datas = [
    (str(project_root / filename), ".")
    for filename in ("index.html", "styles.css", "app.js")
]
hiddenimports = []
if platform.system() == "Windows":
    hiddenimports = [
        "pythoncom",
        "pywintypes",
        "win32timezone",
        "win32com.client",
        "win32print",
    ]

a = Analysis(
    [str(project_root / "launch_app.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
if hasattr(a, "zipfiles"):
    pyz = PYZ(a.pure, a.zipped_data)
    exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [], name="Scan2scanner")
else:
    pyz = PYZ(a.pure)
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="Scan2scanner")