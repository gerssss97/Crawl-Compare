"""Resolución del Excel inicial a cargar al arrancar la app.

Orden de prioridad:
1. config["last_excel_path"] si el archivo sigue existiendo.
2. Primer .xlsx encontrado en ./Data/ junto al binario o al main.py.
3. None — la app arranca sin Excel y la UI lo indica al usuario.
"""

import sys
from pathlib import Path
from typing import Optional

from .services.config_service import ConfigService


def _data_dir() -> Path:
    """Directorio Data/ junto al .exe o al main.py."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "Data"  # type: ignore[attr-defined]
    return Path(__file__).parent.parent / "Data"  # Hoteles/Data/


def resolver_excel_inicial(config: ConfigService) -> Optional[str]:
    """Decide qué Excel cargar al arrancar la app.

    Args:
        config: instancia de ConfigService ya inicializada.

    Returns:
        Path absoluto al Excel a cargar, o None si no se encontró nada.
    """
    last_path_str = config.get_last_excel_path()
    if last_path_str:
        last_path = Path(last_path_str)
        if last_path.is_file():
            return str(last_path)
        # El usuario movió/borró el archivo, limpiamos para no reintentar siempre
        print(f"[excel_resolver] Último Excel ({last_path}) ya no existe. Limpiando config.")
        config.set_last_excel_path(None)

    data_dir = _data_dir()
    if data_dir.is_dir():
        xlsx_files = sorted(data_dir.glob("*.xlsx"))
        if xlsx_files:
            return str(xlsx_files[0])

    return None
