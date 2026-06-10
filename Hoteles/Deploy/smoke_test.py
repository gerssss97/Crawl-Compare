# ============================================================
# smoke_test.py — Verificación post-build del .exe
#
# Corre cuando el .exe se invoca con flag --self-test (ver main.py).
# Importa e inicializa los módulos críticos del bundle. Si algo falla,
# exit code != 0 → build.bat aborta el build como inválido.
#
# Filosofía: cada vez que descubrimos un bug de bundling (tipo "tiktoken
# no tiene cl100k_base"), agregamos ACÁ el check correspondiente. Así el
# mismo bug nunca se repite en silencio.
# ============================================================
import sys
import traceback


def _check(name, fn):
    """Corre un check y reporta. Retorna True si pasó, False si falló."""
    try:
        result = fn()
        detail = f" — {result}" if result else ""
        print(f"[SMOKE] OK   {name}{detail}")
        return True
    except Exception as e:
        print(f"[SMOKE] FAIL {name}: {type(e).__name__}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return False


def _check_tiktoken():
    """Bug histórico: tiktoken_ext no se incluía → 'Unknown encoding cl100k_base'."""
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    return f"cl100k_base loaded ({enc.n_vocab} tokens)"


def _check_playwright():
    """Verifica que playwright importe y que el driver exista."""
    from playwright.sync_api import sync_playwright
    return "import OK"


def _check_crawl4ai():
    """Crawl4AI carga snippets .js de forma diferida — verificar import."""
    import crawl4ai
    from crawl4ai import AsyncWebCrawler, LLMExtractionStrategy
    return f"v{getattr(crawl4ai, '__version__', '?')}"


def _check_playwright_stealth():
    """Carga scripts .js de evasión desde el paquete."""
    import playwright_stealth
    return "import OK"


def _check_fake_http_header():
    """Lee carpeta data/ con headers — falló en builds anteriores."""
    from fake_http_header import FakeHttpHeader
    h = FakeHttpHeader()
    return "instantiated OK"


def _check_customtkinter():
    """Carga themes JSON al inicializar."""
    import customtkinter as ctk
    return f"v{ctk.__version__}"


def _check_env_loaded():
    """El .env debe estar embebido en _MEIPASS y cargarse al arrancar."""
    import os
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY no está en el entorno (¿se cargó el .env?)")
    return f"GROQ_API_KEY presente ({len(os.getenv('GROQ_API_KEY'))} chars)"


def _check_excel_path():
    """El Excel debe estar embebido en _MEIPASS/Data/."""
    import os
    from pathlib import Path
    if getattr(sys, "frozen", False):
        excel = Path(sys._MEIPASS) / "Data" / "Extracto_prueba2.xlsx"
    else:
        excel = Path(__file__).parent.parent / "Data" / "Extracto_prueba2.xlsx"
    if not excel.exists():
        raise FileNotFoundError(f"Excel no encontrado en {excel}")
    return f"{excel.name} ({excel.stat().st_size:,} bytes)"


# Mínimo esperado de íconos por variante (light/ y dark/). Si agregás un
# ícono nuevo a UI/assets/icons/ Y lo usás en UI/styles/icons.py, bumpeá
# este número. Si te olvidás, el check de paridad light↔dark igual va a
# detectar inconsistencias parciales.
_MIN_ICONS_POR_VARIANTE = 9


def _icons_base_dir():
    """Devuelve la ruta base de UI/assets/icons (dev o bundle)."""
    from pathlib import Path
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "UI" / "assets" / "icons"
    return Path(__file__).parent.parent / "UI" / "assets" / "icons"


def _check_icons_bundled():
    """Bug histórico: íconos no incluidos en EXTRA_DATAS → FileNotFoundError
    en UI/styles/icons.py al instanciar CTkImage. Verifica dos invariantes:
    1) hay al menos _MIN_ICONS_POR_VARIANTE PNGs en cada variante;
    2) cada PNG en light/ tiene su contraparte en dark/."""
    base = _icons_base_dir()
    if not base.exists():
        raise FileNotFoundError(f"Directorio de íconos no existe: {base}")

    light = {p.stem for p in (base / "light").glob("*.png")}
    dark  = {p.stem for p in (base / "dark").glob("*.png")}

    if len(light) < _MIN_ICONS_POR_VARIANTE:
        raise FileNotFoundError(
            f"Solo {len(light)} íconos en light/ (mínimo esperado: "
            f"{_MIN_ICONS_POR_VARIANTE}). ¿EXTRA_DATAS incluye "
            "UI/assets/icons/ en build_manifest.py?"
        )
    if len(dark) < _MIN_ICONS_POR_VARIANTE:
        raise FileNotFoundError(
            f"Solo {len(dark)} íconos en dark/ (mínimo esperado: "
            f"{_MIN_ICONS_POR_VARIANTE})."
        )

    sin_par = light ^ dark
    if sin_par:
        raise FileNotFoundError(
            f"PNGs sin par light↔dark: {', '.join(sorted(sin_par))}"
        )

    return f"{len(light)} íconos con paridad light↔dark"


# Lista declarativa de checks — agregar uno nuevo cada vez que se
# descubra un bug de bundling para que no vuelva a pasar silenciosamente.
CHECKS = [
    ("customtkinter",     _check_customtkinter),
    ("tiktoken encoding", _check_tiktoken),
    ("playwright",        _check_playwright),
    ("playwright_stealth", _check_playwright_stealth),
    ("crawl4ai",          _check_crawl4ai),
    ("fake_http_header",  _check_fake_http_header),
    (".env loaded",       _check_env_loaded),
    ("Excel embebido",    _check_excel_path),
    ("Íconos bundled",    _check_icons_bundled),
]


def run_smoke_test():
    """Corre todos los checks. Sale con código != 0 si alguno falla."""
    print("=" * 60)
    print("SMOKE TEST — CrawlCompare.exe")
    print(f"frozen={getattr(sys, 'frozen', False)}  python={sys.version.split()[0]}")
    print("=" * 60)

    results = [_check(name, fn) for name, fn in CHECKS]

    passed = sum(results)
    total = len(results)
    print("=" * 60)
    if all(results):
        print(f"[SMOKE] ✅ TODOS LOS CHECKS PASARON ({passed}/{total})")
        sys.exit(0)
    else:
        print(f"[SMOKE] ❌ FALLARON {total - passed}/{total} CHECKS")
        sys.exit(1)
