"""Shim de backward-compatibility — importar desde los módulos específicos.

  Colores  → UI_qt/styles/palette.py
  Tamaños  → UI_qt/styles/constants.py
  QSS      → UI_qt/styles/stylesheet.py
"""

from UI_qt.styles.palette import Palette, LIGHT, DARK, PALETTES
from UI_qt.styles.stylesheet import build_qss

__all__ = ["Palette", "LIGHT", "DARK", "PALETTES", "build_qss"]
