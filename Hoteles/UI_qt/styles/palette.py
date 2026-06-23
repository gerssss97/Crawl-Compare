"""Tokens de color del design system Qt (dual-mode light/dark).

Fuente única de verdad para colores. Importar desde acá, no desde theme.py.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    """Tokens de color de un tema (light o dark)."""
    name: str
    bg: str
    surface: str
    border: str
    chip: str
    chip_text: str
    header_bg: str
    header_text: str
    primary: str
    primary_hover: str
    accent: str
    text_primary: str
    text_secondary: str
    text_muted: str
    input_bg: str
    shadow_rgba: tuple
    shadow_blur: int


LIGHT = Palette(
    name="light",
    bg="#E2E8F0", surface="#FFFFFF", border="#CBD5E1",
    chip="#334155", chip_text="#FFFFFF",
    header_bg="#1E293B", header_text="#FFFFFF",
    primary="#2563EB", primary_hover="#1D4ED8", accent="#2563EB",
    text_primary="#1E293B", text_secondary="#64748B", text_muted="#94A3B8",
    input_bg="#F1F5F9",
    shadow_rgba=(15, 23, 42, 65), shadow_blur=12,
)

DARK = Palette(
    name="dark",
    bg="#0F172A", surface="#1E293B", border="#334155",
    chip="#334155", chip_text="#F8FAFC",
    header_bg="#0B1220", header_text="#F8FAFC",
    primary="#2563EB", primary_hover="#1D4ED8", accent="#60A5FA",
    text_primary="#F1F5F9", text_secondary="#94A3B8", text_muted="#64748B",
    input_bg="#0F172A",
    shadow_rgba=(0, 0, 0, 64), shadow_blur=10,
)

PALETTES: dict[str, Palette] = {"light": LIGHT, "dark": DARK}
