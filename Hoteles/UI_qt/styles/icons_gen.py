"""Genera iconos (chevrons) como PNG en runtime con QPainter.

Por que PNG y no SVG en el QSS: en este entorno conda PySide6 no resuelve los
data URI de SVG en QSS (ni utf8 ni base64) porque el plugin qsvg no carga para ese
caso -> la flecha quedaba invisible. Un cuadrado solido en ::down-arrow SI se ve, o
sea el subcontrol funciona; el problema es solo la imagen SVG. Dibujar el chevron a
un QPixmap y guardarlo como PNG por path es 100% confiable (no depende de plugins).

Los PNG se cachean en UI_qt/styles/_generated/ (key = direccion+color+size).
"""

import os
import sys
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt, QPointF


def _gen_dir() -> str:
    """En modo frozen los PNGs vienen bundleados en _MEIPASS (read-only).
    En dev se escriben junto al módulo como antes."""
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "UI_qt", "styles", "_generated")
    return os.path.join(os.path.dirname(__file__), "_generated")


def _ensure_dir():
    if not getattr(sys, "frozen", False):
        os.makedirs(_gen_dir(), exist_ok=True)


def chevron_png(direction: str, color: str, size: int = 12, scale: int = 2) -> str:
    """Devuelve el path a un PNG con un chevron en la direccion/color dados.

    Args:
        direction: "down" | "left" | "right".
        color: color del trazo (hex, ej. "#64748B").
        size: lado del icono en px logicos.
        scale: factor de supersampling para bordes nitidos en pantallas HiDPI.
    Returns:
        Ruta absoluta al PNG generado (con forward slashes para usar en QSS url()).
    """
    _ensure_dir()
    key = f"chevron_{direction}_{color.lstrip('#')}_{size}x{scale}.png"
    path = os.path.join(_gen_dir(), key)
    if not os.path.exists(path):
        _draw(path, direction, color, size, scale)
    # QSS url() quiere forward slashes incluso en Windows
    return path.replace("\\", "/")


def _draw(path, direction, color, size, scale):
    s = size * scale
    pm = QPixmap(s, s)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    pen = QPen(QColor(color))
    pen.setWidthF(1.6 * scale)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)

    # Coordenadas relativas (0..1) escaladas a s
    def pt(x, y):
        return QPointF(x * s, y * s)

    if direction == "down":
        pts = [pt(0.18, 0.34), pt(0.5, 0.66), pt(0.82, 0.34)]
    elif direction == "left":
        pts = [pt(0.64, 0.18), pt(0.34, 0.5), pt(0.64, 0.82)]
    else:  # right
        pts = [pt(0.36, 0.18), pt(0.66, 0.5), pt(0.36, 0.82)]

    p.drawPolyline(pts)
    p.end()
    pm.save(path, "PNG")
