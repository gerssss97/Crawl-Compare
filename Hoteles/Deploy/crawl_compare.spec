# crawl_compare.spec
# Configuración de PyInstaller. NO modificar listas de paquetes acá —
# usar Deploy/build_manifest.py (es el "package.json" del deploy).
import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules

# Directorio raíz del proyecto (Hoteles/)
ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

# Importar el manifest declarativo
sys.path.insert(0, SPECPATH)
from build_manifest import (
    PACKAGES_COLLECT_ALL,
    PACKAGES_SUBMODULES,
    EXTRA_HIDDEN_IMPORTS,
    EXCLUDES,
    resolve_datas,
    resolve_binaries,
)

# Acumular datas/binaries/hiddenimports desde collect_all
all_datas, all_binaries, all_hiddenimports = [], [], []
for pkg in PACKAGES_COLLECT_ALL:
    d, b, h = collect_all(pkg)
    all_datas += d
    all_binaries += b
    all_hiddenimports += h

# Submódulos puros (solo hiddenimports)
for pkg in PACKAGES_SUBMODULES:
    all_hiddenimports += collect_submodules(pkg)

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=all_binaries,
    datas=[
        *all_datas,
        *resolve_datas(ROOT),
        *resolve_binaries(),
    ],
    hiddenimports=[
        *all_hiddenimports,
        *EXTRA_HIDDEN_IMPORTS,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="CrawlCompare",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,   # True mientras se testea, cambiar a False para distribuir
    icon=None,
)
