"""Generador del QSS global desde las constantes del design system.

Importa tokens de palette.py y constants.py — no hardcodea ningún valor.
"""

from UI_qt.styles.spacing import Spacing
from UI_qt.styles.typography import Typography
from UI_qt.styles.palette import Palette, PALETTES
from UI_qt.styles.constants import (
    INPUT_HEIGHT,
    BUTTON_HEIGHT_PRIMARY,
    STEPPER_HEIGHT,
    MESSAGEBOX_BTN_MIN_W,
)
from UI_qt.styles.icons_gen import chevron_png


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
    QLabel#sectionLabel {{ color: {p.text_secondary}; font-size: {Typography.SMALL + 1}px; font-weight: 600; }}
    QLabel#mutedLabel {{ color: {p.text_muted}; font-size: {Typography.SMALL}px; }}
    QLabel#fieldLabel {{ color: {p.text_secondary}; font-size: {Typography.SMALL + 1}px; font-weight: 600; }}

    /* ===== Inputs ===== */
    QLineEdit, QComboBox, QDateEdit {{
        background-color: {p.input_bg};
        border: 1px solid {p.border};
        border-radius: {r_md}px;
        padding: 6px 10px;
        min-height: {INPUT_HEIGHT}px;
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
        border: 1px solid {p.border};
        border-radius: {r_md}px;
        outline: none;
        padding: 4px 0;
    }}
    QComboBox QAbstractItemView::item {{
        background-color: {p.surface};
        color: {p.text_primary};
        padding: 6px 12px;
        border-radius: {r_sm}px;
        min-height: 26px;
    }}
    QComboBox QAbstractItemView::item:hover,
    QComboBox QAbstractItemView::item:focus {{
        background-color: {p.chip};
        color: {p.chip_text};
    }}
    QComboBox QAbstractItemView::item:selected {{
        background-color: {p.primary};
        color: #FFFFFF;
    }}
    QComboBox QAbstractItemView::indicator {{
        width: 0;
        image: none;
    }}

    /* ===== Completer popup (QtLabeledCombo) ===== */
    QWidget#completerPopupViewport {{
        background-color: {p.surface};
    }}
    QListView#completerPopup {{
        background-color: {p.surface};
        color: {p.text_primary};
        border: 1px solid {p.border};
        border-radius: {r_md}px;
        outline: none;
        padding: 0 3px;
    }}
    QListView#completerPopup::item {{
        background-color: {p.surface};
        color: {p.text_primary};
        padding: 4px 10px;
        min-height: 20px;
    }}
    QListView#completerPopup::item:hover,
    QListView#completerPopup::item:focus {{
        background-color: {p.chip};
        color: {p.chip_text};
    }}
    QListView#completerPopup::item:selected {{
        background-color: {p.primary};
        color: #FFFFFF;
    }}
    QListView#completerPopup::indicator {{
        width: 0;
        image: none;
    }}
    QListView#completerPopup QScrollBar:vertical {{
        background: {p.border};
        width: 6px;
        margin: 4px 2px 4px 0;
        border-radius: 3px;
    }}
    QListView#completerPopup QScrollBar::handle:vertical {{
        background: {p.text_muted};
        border-radius: 3px;
        min-height: 20px;
    }}
    QListView#completerPopup QScrollBar::add-line:vertical,
    QListView#completerPopup QScrollBar::sub-line:vertical {{ height: 0; }}
    QListView#completerPopup QScrollBar::add-page:vertical,
    QListView#completerPopup QScrollBar::sub-page:vertical {{ background: transparent; }}

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
    QCalendarWidget QMenu {{ background-color: {p.surface}; color: {p.text_primary}; }}
    QCalendarWidget QSpinBox {{
        background-color: {p.input_bg}; color: {p.text_primary};
        border: 1px solid {p.border}; border-radius: {r_sm}px;
    }}

    /* ===== Botones ===== */
    QPushButton#btnPrimary {{
        background-color: {p.primary}; color: #FFFFFF;
        border: none; border-radius: {r_lg - 2}px;
        min-height: {BUTTON_HEIGHT_PRIMARY}px; padding: 0 {Spacing.LG}px; font-size: {Typography.BODY}px; font-weight: bold;
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

    /* ===== Modales / contenedores ===== */
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
        min-height: {STEPPER_HEIGHT}px;
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
        padding: 5px 16px; min-width: {MESSAGEBOX_BTN_MIN_W}px;
    }}
    QMessageBox QPushButton:hover {{ border: 1px solid {p.primary}; }}

    /* ===== Hints / shortcuts ===== */
    QLabel#shortcutHint {{
        color: {p.text_muted}; font-size: {Typography.SMALL - 1}px;
    }}
    """
