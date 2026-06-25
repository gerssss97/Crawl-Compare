"""Iconos QIcon desde los PNG de Feather (reutiliza UI/assets/icons light/dark).

En este entorno conda el plugin qsvg de Qt no carga (Qt del wheel vs plugin de
conda-forge no coinciden), asi que SVG no esta disponible. Se usan los PNG de Feather
ya generados para la version CTk. QIcon es superior a CTkImage (maneja estados/tamaños),
aunque sin escalado vectorial.

Los iconos tienen variante light (trazo oscuro, para fondos claros) y dark (trazo claro,
para el header oscuro). icon(name, on_dark=...) elige la variante segun el fondo.
"""

from pathlib import Path
from PySide6.QtGui import QIcon

_BASE = Path(__file__).parent.parent / "assets" / "icons"

# Mapa nombre logico -> archivo
_NAMES = {
    "clock": "clock",
    "settings": "settings",
    "folder": "folder",
    "home": "home",
    "trash": "trash-2",
    "dollar": "dollar-sign",
    "alert": "alert-triangle",
    "x_circle": "x-circle",
    "check_circle": "check-circle",
}

_cache = {}


def icon(name: str, on_dark: bool = False) -> QIcon:
    """Devuelve el QIcon del nombre logico dado.

    Args:
        name: clave de _NAMES (ej. "clock", "settings").
        on_dark: True si el icono va sobre fondo oscuro (header) -> usa variante 'dark'
                 (trazo claro). False -> variante 'light' (trazo oscuro).
    """
    archivo = _NAMES.get(name, name)
    variante = "dark" if on_dark else "light"
    key = (archivo, variante)
    if key not in _cache:
        path = _BASE / variante / f"{archivo}.png"
        _cache[key] = QIcon(str(path))
    return _cache[key]
