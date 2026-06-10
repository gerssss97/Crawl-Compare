"""Hook PostToolUse: avisa cuando se modifican archivos del build (manifest, spec, assets)."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Archivos del build cuya modificación amerita rebuildear + correr smoke test.
BUILD_FILES = [
    "Hoteles/Deploy/build_manifest.py",
    "Hoteles/Deploy/crawl_compare.spec",
    "Hoteles/Deploy/smoke_test.py",
    "Hoteles/Deploy/startup_check.py",
    "Hoteles/Deploy/error_logger.py",
    "Hoteles/Deploy/splash.py",
    "Hoteles/main.py",
    "Hoteles/debug_config.py",
]

# Carpetas cuyos cambios suelen requerir actualizar EXTRA_DATAS.
ASSET_DIRS = [
    "Hoteles/UI/assets/",
    "Hoteles/Data/",
]


def normalizar(ruta: str) -> str:
    return ruta.replace("\\", "/")


def es_archivo_build(ruta: str) -> bool:
    ruta_norm = normalizar(ruta)
    return any(ruta_norm.endswith(f) for f in BUILD_FILES)


def es_asset(ruta: str) -> bool:
    ruta_norm = normalizar(ruta)
    return any(d in ruta_norm for d in ASSET_DIRS)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_input = payload.get("tool_input", {}) or {}
    ruta = tool_input.get("file_path") or tool_input.get("filePath") or ""
    if not ruta:
        sys.exit(0)

    if es_archivo_build(ruta):
        print(
            "[build-deps] Modificaste un archivo del build "
            f"({Path(ruta).name}). Antes de distribuir corré:\n"
            "  Deploy\\build.bat\n"
            "El smoke test post-build verifica que todos los recursos "
            "críticos lleguen al bundle.",
            file=sys.stderr,
        )
    elif es_asset(ruta):
        print(
            f"[build-deps] Tocaste un asset ({Path(ruta).name}). "
            "Verificá que esté declarado en Hoteles/Deploy/build_manifest.py "
            "(EXTRA_DATAS) y agregalo a smoke_test.py si es crítico.",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
