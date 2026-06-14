# ============================================================
# build_manifest.py — Manifiesto declarativo del bundle del .exe
#
# Este es el archivo "package.json" del deploy: declara TODO lo que entra
# al .exe. El crawl_compare.spec lee de acá — modificá ESTE archivo, no el .spec.
#
# Cuando agregues una dependencia nueva al proyecto y falle en runtime
# dentro del .exe (típicamente con "Plugins found: []" o ModuleNotFoundError),
# agregala a la sección correspondiente:
#   - PACKAGES_COLLECT_ALL → paquetes que tienen datas/binaries propios
#   - PACKAGES_SUBMODULES  → paquetes con submódulos detectados por nombre
#   - EXTRA_HIDDEN_IMPORTS → módulos cargados dinámicamente (sin import explícito)
#   - EXTRA_DATAS          → archivos de recursos del proyecto (Excel, .env)
#   - EXTERNAL_BINARIES    → binarios externos al venv (Chromium, drivers)
# ============================================================
import os


# Paquetes que se pasan a collect_all() → trae datas + binaries + hiddenimports
# de TODO el árbol del paquete (incluyendo dependencias transitivas declaradas).
PACKAGES_COLLECT_ALL = [
    "PySide6",              # DLLs Qt + plugins (platforms, styles, imageformats)
    "numpy",                # extensiones C (.pyd) + DLLs MKL/OpenBLAS de conda-forge
    "crawl4ai",             # snippets .js de scraping
    "playwright",           # driver node.exe + package JS
    "playwright_stealth",   # scripts .js de evasión
    "fake_http_header",     # carpeta data/ con headers
    "tiktoken",             # tokenizer base (BPE rank files)
    "tiktoken_ext",         # CRÍTICO: encodings (cl100k_base, etc.) — plugin-style
    "litellm",              # provider configs (Groq, OpenAI, etc.)
]

# Paquetes para collect_submodules() → solo hiddenimports, sin datas.
PACKAGES_SUBMODULES = [
    "openpyxl",
    "rapidfuzz",
    "pydantic",
]

# Hidden imports adicionales (módulos cargados dinámicamente o con nombres no estándar).
EXTRA_HIDDEN_IMPORTS = [
    "dotenv",
    # PySide6: módulos usados en el proyecto
    "PySide6.QtWidgets",
    "PySide6.QtCore",
    "PySide6.QtGui",
]

# Recursos del proyecto: (origen_relativo_a_ROOT, destino_en_MEIPASS)
# ROOT = Hoteles/
EXTRA_DATAS = [
    ("Data/Extracto_prueba2.xlsx", "Data"),
    (".env", "."),
    # Íconos Feather PNG (compartidos entre CTk y Qt)
    ("UI/assets/icons/light", "UI/assets/icons/light"),
    ("UI/assets/icons/dark",  "UI/assets/icons/dark"),
    # Chevrons pre-generados: en _MEIPASS son read-only, icons_gen.py los lee sin regenerar
    ("UI_qt/styles/_generated", "UI_qt/styles/_generated"),
]

# Binarios externos al venv: rutas absolutas en el sistema del developer.
_MKL_BIN = r"C:\Users\German Lucero\anaconda3\envs\crawler\Library\bin"

# DLLs de MKL que numpy 2.x (conda-forge) necesita en runtime.
# Solo el subset mínimo — excluimos blacs/scalapack/cdft (HPC distribuido).
_MKL_DLLS = [
    "mkl_core.3.dll",
    "mkl_rt.3.dll",
    "mkl_intel_thread.3.dll",
    "mkl_sequential.3.dll",
    "mkl_def.3.dll",
    "mkl_avx2.3.dll",
    "mkl_avx512.3.dll",
    "mkl_avx10.3.dll",
    "mkl_mc3.3.dll",
    "mkl_vml_def.3.dll",
    "mkl_vml_avx2.3.dll",
    "mkl_vml_avx512.3.dll",
    "mkl_vml_avx10.3.dll",
    "mkl_vml_cmpt.3.dll",
    "mkl_vml_mc3.3.dll",
]

EXTERNAL_BINARIES = [
    {
        "name": "Chromium (Playwright)",
        "source": r"C:\Users\German Lucero\AppData\Local\ms-playwright\chromium-1181",
        "dest":   r"playwright/driver/package/.local-browsers/chromium-1181",
    },
    {
        "name": "Playwright driver (node.exe + package JS)",
        "source": r"C:\Users\German Lucero\anaconda3\envs\crawler\Lib\site-packages\playwright\driver",
        "dest":   r"playwright/driver",
    },
    # MKL: una entrada por DLL, todas van a la raíz de _internal (junto a python312.dll)
    *[{"name": f"MKL {dll}", "source": f"{_MKL_BIN}\\{dll}", "dest": "."} for dll in _MKL_DLLS],
]

# Módulos a EXCLUIR del bundle.
# Los subpaquetes de PySide6 que NO usamos pesan mucho (~168MB en PySide6-addons).
# Listamos explícitamente los que sí usamos y excluimos el resto pesado.
EXCLUDES = [
    "Tests",
    # Tkinter ya no se usa en ningún lado
    "tkinter",
    "_tkinter",
    "customtkinter",
    # Qt: submódulos que no usamos y que inflan el bundle
    "PySide6.QtWebEngine",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebChannel",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DExtras",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets",
    "PySide6.QtQuickControls2",
    "PySide6.QtQml",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtBluetooth",
    "PySide6.QtNfc",
    "PySide6.QtSensors",
    "PySide6.QtLocation",
    "PySide6.QtPositioning",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtStateMachine",
    "PySide6.QtTextToSpeech",
    "PySide6.QtVirtualKeyboard",
    "PySide6.QtWebSockets",
    "PySide6.QtXml",
    "PySide6.QtDesigner",
    "PySide6.QtUiTools",
    "PySide6.QtHelp",
    "PySide6.QtTest",
]


def resolve_datas(root):
    """Resuelve EXTRA_DATAS a rutas absolutas usando ROOT del proyecto."""
    return [(os.path.join(root, src), dst) for src, dst in EXTRA_DATAS]


def resolve_binaries():
    """Devuelve EXTERNAL_BINARIES en el formato (source, dest) que espera PyInstaller."""
    return [(b["source"], b["dest"]) for b in EXTERNAL_BINARIES]
