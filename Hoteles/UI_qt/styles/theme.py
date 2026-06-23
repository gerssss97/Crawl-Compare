"""Paletas dual-mode (light/dark) y generador de QSS desde las constantes del proyecto.

Reutiliza Spacing y Typography de UI/styles (fuente unica de verdad para radios,
espaciados y tipografia). Define dos paletas aprobadas en el mockup de Figma y
genera el stylesheet global con build_qss(theme). QSS no tiene box-shadow: las
sombras de las cards se aplican aparte con QGraphicsDropShadowEffect (ver shadow()).
"""

from dataclasses import dataclass
from UI.styles import Spacing, Typography


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
    # sombra de card: (rgba) como tupla para QGraphicsDropShadowEffect
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
    shadow_rgba=(15, 23, 42, 65), shadow_blur=12,  # negro ~25% (alpha 0..255)
)

DARK = Palette(
    name="dark",
    bg="#0F172A", surface="#1E293B", border="#334155",
    chip="#334155", chip_text="#F8FAFC",
    header_bg="#0B1220", header_text="#F8FAFC",
    primary="#2563EB", primary_hover="#1D4ED8", accent="#60A5FA",
    text_primary="#F1F5F9", text_secondary="#94A3B8", text_muted="#64748B",
    input_bg="#0F172A",
    shadow_rgba=(0, 0, 0, 64), shadow_blur=10,     # negro ~25%
)

PALETTES = {"light": LIGHT, "dark": DARK}


def build_qss(theme: str = "light") -> str:
    """Genera el QSS global para el tema dado desde las constantes del proyecto.

    Args:
        theme: "light" o "dark".
    Returns:
        El stylesheet completo como string, listo para app.setStyleSheet().
    """
    p = PALETTES[theme]
    fam = Typography.FAMILY
    r_sm, r_md, r_lg = Spacing.RADIUS_SM, Spacing.RADIUS_MD, Spacing.RADIUS_LG
    primary_tint = "#EFF6FF" if theme == "light" else "#172554"
    primary_tint_border = "#BFDBFE" if theme == "light" else "#1E40AF"

    # Flechas chevron como PNG generado en runtime (QPainter). Data URI de SVG en
    # QSS no se renderiza en este entorno conda (plugin qsvg). PNG por path es fiable.
    from UI_qt.styles.icons_gen import chevron_png

    chev_down = chevron_png("down", p.text_secondary)
    chev_left = chevron_png("left", p.header_text)
    chev_right = chevron_png("right", p.header_text)

    return f"""
    /* ===== Base =====
       OJO: no pintar background-color en el selector QWidget generico: QLabel y
       QPushButton heredarian ese fondo y se veria un rectangulo feo (sobre todo
       sobre el header oscuro). El fondo se pinta solo en contenedores concretos
       (QMainWindow, #header, #card...). Los labels van transparentes. */
    QWidget {{
        color: {p.text_primary};
        font-family: "{fam}", "Segoe UI", Arial, sans-serif;
        font-size: {Typography.BODY - 1}px;
    }}
    QMainWindow {{ background-color: {p.bg}; }}
    QMainWindow > QWidget {{ background-color: {p.bg}; }}
    QLabel {{ background: transparent; }}

    /* ===== Header ===== */
    QFrame#header {{ background-color: {p.header_bg}; border: none; }}
    QLabel#headerTitle {{ color: {p.header_text}; font-size: {Typography.H2}px; font-weight: bold; }}
    QLabel#headerExcel {{ color: {p.text_secondary}; font-size: {Typography.SMALL}px; }}
    QPushButton#headerChip {{
        background-color: {p.chip}; color: {p.chip_text};
        border: none; border-radius: {r_md}px;
        padding: 6px 14px; font-size: {Typography.SMALL}px;
    }}
    QPushButton#headerChip:hover {{ background-color: {p.primary}; }}
    QPushButton#headerGear {{ background-color: transparent; border: none; color: {p.header_text}; font-size: 18px; }}
    QPushButton#headerGear:hover {{ background-color: {p.chip}; border-radius: {r_md}px; }}

    /* ===== Cards ===== */
    QFrame#card {{
        background-color: {p.surface};
        border: 1px solid {p.border};
        border-radius: {r_lg}px;
    }}
    QLabel#cardTitle {{ color: {p.text_primary}; font-size: {Typography.SMALL + 1}px; font-weight: bold; }}
    QLabel#sectionLabel {{ color: {p.text_secondary}; font-size: {Typography.SMALL}px; font-weight: 600; }}
    QLabel#mutedLabel {{ color: {p.text_muted}; font-size: {Typography.SMALL - 1}px; }}
    QLabel#fieldLabel {{ color: {p.text_secondary}; font-size: {Typography.SMALL}px; font-weight: 600; }}

    /* ===== Inputs ===== */
    QLineEdit, QComboBox, QDateEdit {{
        background-color: {p.input_bg};
        border: 1px solid {p.border};
        border-radius: {r_md}px;
        padding: 6px 10px;
        min-height: 26px;
        color: {p.text_primary};
    }}
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{ border: 1px solid {p.primary}; }}
    QComboBox::drop-down, QDateEdit::drop-down {{
        border: none; width: 26px; subcontrol-origin: padding; subcontrol-position: center right;
    }}
    QComboBox::down-arrow, QDateEdit::down-arrow {{
        image: url("{chev_down}"); width: 12px; height: 12px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {p.surface};
        color: {p.text_primary};
        selection-background-color: {p.primary};
        selection-color: #FFFFFF;
        border: none;
        outline: none;
    }}

    /* ===== Calendario (popup de QDateEdit) ===== */
    QCalendarWidget QWidget {{ alternate-background-color: {p.surface}; }}
    QCalendarWidget QAbstractItemView:enabled {{
        background-color: {p.surface};
        color: {p.text_primary};
        selection-background-color: {p.primary};
        selection-color: #FFFFFF;
        outline: none;
    }}
    QCalendarWidget QAbstractItemView:disabled {{ color: {p.text_muted}; }}
    /* barra de navegacion superior (mes/anio + flechas) */
    QCalendarWidget QWidget#qt_calendar_navigationbar {{ background-color: {p.header_bg}; }}
    QCalendarWidget QToolButton {{
        color: {p.header_text}; background-color: transparent;
        border: none; border-radius: {r_sm}px; padding: 4px 8px; margin: 2px;
        font-size: {Typography.SMALL}px; font-weight: 600;
    }}
    QCalendarWidget QToolButton:hover {{ background-color: {p.primary}; }}
    QCalendarWidget QToolButton::menu-indicator {{ image: none; }}
    QCalendarWidget #qt_calendar_prevmonth {{
        qproperty-icon: none; image: url("{chev_left}"); width: 14px; height: 14px;
    }}
    QCalendarWidget #qt_calendar_nextmonth {{
        qproperty-icon: none; image: url("{chev_right}"); width: 14px; height: 14px;
    }}
    /* dropdowns de mes/anio dentro del calendario */
    QCalendarWidget QMenu {{ background-color: {p.surface}; color: {p.text_primary}; }}
    QCalendarWidget QSpinBox {{
        background-color: {p.input_bg}; color: {p.text_primary};
        border: 1px solid {p.border}; border-radius: {r_sm}px;
    }}

    /* ===== Botones ===== */
    QPushButton#btnPrimary {{
        background-color: {p.primary}; color: #FFFFFF;
        border: none; border-radius: {r_lg - 2}px;
        min-height: 44px; padding: 0 24px; font-size: {Typography.BODY}px; font-weight: bold;
    }}
    QPushButton#btnPrimary:hover {{ background-color: {p.primary_hover}; }}
    QPushButton#btnPrimarySmall {{
        background-color: {p.primary}; color: #FFFFFF;
        border: none; border-radius: {r_sm}px;
        padding: 4px 14px; font-size: {Typography.SMALL}px; font-weight: 600;
    }}
    QPushButton#btnPrimarySmall:hover {{ background-color: {p.primary_hover}; }}
    QPushButton#btnSecondary {{
        background-color: {p.input_bg}; color: {p.text_secondary};
        border: 1px solid {p.border}; border-radius: {r_sm}px;
        padding: 4px 10px; font-size: {Typography.SMALL}px;
    }}
    QPushButton#btnSecondary:hover {{ border: 1px solid {p.primary}; color: {p.primary}; }}
    QPushButton#btnOutline {{
        background-color: {p.border}; color: {p.text_secondary};
        border: 1px solid {p.text_muted}; border-radius: {r_sm}px;
        padding: 4px 12px; font-size: {Typography.SMALL}px;
    }}
    QPushButton#btnOutline:hover, QPushButton#btnOutline:focus, QPushButton#btnOutline:pressed {{
        background-color: {p.border}; border: 1px solid {p.primary}; color: {p.primary};
    }}
    QPushButton#btnGhost {{
        background-color: {p.surface}; color: {p.text_secondary};
        border: 1.5px solid {p.border}; border-radius: {r_sm}px;
        padding: 4px 14px; font-size: {Typography.SMALL}px;
    }}
    QPushButton#btnGhost:hover, QPushButton#btnGhost:focus {{
        border: 1.5px solid {p.primary}; color: {p.primary};
    }}
    QPushButton#btnGhost:pressed {{
        background-color: {primary_tint}; border: 1.5px solid {p.primary}; color: {p.primary};
    }}
    QPushButton#varChip {{
        background-color: {p.input_bg}; color: {p.text_secondary};
        border: 1px solid {p.border}; border-radius: {r_sm}px;
        padding: 2px 7px; font-size: {Typography.SMALL - 1}px;
        font-family: "Consolas", "Courier New", monospace;
    }}
    QPushButton#varChip:hover, QPushButton#varChip:focus, QPushButton#varChip:pressed {{ border: 1px solid {p.primary}; color: {p.primary}; }}

    /* ===== Panel precio / periodos ===== */
    QLabel#priceValue {{ color: {p.accent}; font-size: {Typography.PRECIO + 2}px; font-weight: bold; }}
    QFrame#chipRow {{ background-color: {p.input_bg}; border: 1px solid {p.border}; border-radius: {r_md}px; }}
    QFrame#chipRowExpanded {{ background-color: {p.input_bg}; border: 1px solid {p.primary}; border-radius: {r_md}px; }}
    QLabel#accentValue {{ color: {p.accent}; font-weight: bold; }}

    /* ===== Scrollbars ===== */
    QScrollBar:vertical {{ background: transparent; width: {Spacing.SCROLLBAR_WIDTH}px; margin: 0; }}
    QScrollBar::handle:vertical {{ background: {p.border}; border-radius: 6px; min-height: 30px; }}
    QScrollBar::handle:vertical:hover {{ background: {p.text_muted}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

    /* ===== Modales / contenedores =====
       Sin esto, QDialog/QTextBrowser/QScrollArea heredan el fondo del sistema
       (negro), rompiendo el light mode. Se fijan al fondo del tema. */
    QDialog {{ background-color: {p.bg}; }}
    QTextEdit, QTextBrowser {{
        background-color: {p.surface};
        color: {p.text_primary};
        border: 1px solid {p.border};
        border-radius: {r_md}px;
    }}
    QScrollArea {{ background-color: transparent; border: none; }}
    QScrollArea > QWidget > QWidget {{ background-color: transparent; }}

    /* ===== Tabs (QConfigModal) ===== */
    QTabWidget::pane {{ border: 1px solid {p.border}; border-radius: {r_md}px; background-color: {p.surface}; }}
    QTabBar::tab {{
        background-color: {p.input_bg}; color: {p.text_secondary};
        border: 1px solid {p.border}; border-bottom: none;
        border-top-left-radius: {r_sm}px; border-top-right-radius: {r_sm}px;
        padding: 6px 14px; margin-right: 2px;
    }}
    QTabBar::tab:selected {{ background-color: {p.primary}; color: #FFFFFF; }}
    QTabBar::tab:hover:!selected {{ color: {p.text_primary}; }}

    /* ===== Stepper (huéspedes / enteros) ===== */
    QFrame#spinStepper {{
        background-color: {p.input_bg};
        border: 1px solid {p.border};
        border-radius: {r_md}px;
        min-height: 34px;
    }}
    QFrame#spinStepper[focused="true"] {{ border: 1px solid {p.primary}; }}
    QPushButton#stepperBtn {{
        background: transparent; border: none;
        color: {p.text_secondary}; font-size: 15px;
        border-radius: {r_sm}px; padding: 0;
    }}
    QPushButton#stepperBtn:hover {{ color: {p.primary}; background-color: {primary_tint}; }}
    QPushButton#stepperBtn:pressed {{ background-color: {primary_tint_border}; color: {p.primary}; }}
    QPushButton#stepperBtn[active="true"] {{ background-color: {primary_tint_border}; color: {p.primary}; }}
    QFrame#spinStepper QLineEdit {{
        background: transparent; border: none; border-radius: 0;
        padding: 0; min-height: 0;
        color: {p.text_primary}; font-weight: 600;
    }}
    QFrame#spinStepper QLineEdit:focus {{ border: none; }}

    /* ===== QMessageBox ===== */
    QMessageBox {{ background-color: {p.bg}; }}
    QMessageBox QLabel {{ color: {p.text_primary}; }}
    QMessageBox QPushButton {{
        background-color: {p.input_bg}; color: {p.text_primary};
        border: 1px solid {p.border}; border-radius: {r_sm}px;
        padding: 5px 16px; min-width: 70px;
    }}
    QMessageBox QPushButton:hover {{ border: 1px solid {p.primary}; }}
    """
