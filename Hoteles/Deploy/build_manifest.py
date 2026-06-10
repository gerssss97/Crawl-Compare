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
# Usar para paquetes con archivos .js/.json/.data internos.
PACKAGES_COLLECT_ALL = [
    "customtkinter",        # themes JSON + assets
    "crawl4ai",             # snippets .js de scraping
    "playwright",           # driver node.exe + package JS
    "playwright_stealth",   # scripts .js de evasión
    "fake_http_header",     # carpeta data/ con headers
    "tiktoken",             # tokenizer base (BPE rank files)
    "tiktoken_ext",         # CRÍTICO: encodings (cl100k_base, etc.) — plugin-style
    "litellm",              # provider configs (Groq, OpenAI, etc.)
]

# Paquetes para collect_submodules() → solo hiddenimports, sin datas.
# Usar para paquetes Python puro donde PyInstaller no detecta todos los submódulos.
PACKAGES_SUBMODULES = [
    "openpyxl",
    "rapidfuzz",
    "pydantic",
]

# Hidden imports adicionales (módulos cargados dinámicamente o con nombres no estándar).
EXTRA_HIDDEN_IMPORTS = [
    "dotenv",
    "tkinter",
    "tkinter.ttk",
]

# Recursos del proyecto: (origen_relativo_a_ROOT, destino_en_MEIPASS)
# ROOT = Hoteles/
#
# Para incluir un DIRECTORIO completo, pasar la carpeta como origen — PyInstaller
# resuelve glob internamente. Verificar siempre con smoke_test que los assets
# críticos llegan al bundle.
EXTRA_DATAS = [
    ("Data/Extracto_prueba2.xlsx", "Data"),
    (".env", "."),
    ("UI/assets/icons/light", "UI/assets/icons/light"),
    ("UI/assets/icons/dark",  "UI/assets/icons/dark"),
]

# Binarios externos al venv: rutas absolutas en el sistema del developer.
# Si el path cambia (ej: Playwright actualiza Chromium), actualizar acá.
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
]

# Módulos a EXCLUIR del bundle (carpetas de tests, etc.)
EXCLUDES = ["Tests"]


def resolve_datas(root):
    """Resuelve EXTRA_DATAS a rutas absolutas usando ROOT del proyecto."""
    return [(os.path.join(root, src), dst) for src, dst in EXTRA_DATAS]


def resolve_binaries():
    """Devuelve EXTERNAL_BINARIES en el formato (source, dest) que espera PyInstaller."""
    return [(b["source"], b["dest"]) for b in EXTERNAL_BINARIES]
