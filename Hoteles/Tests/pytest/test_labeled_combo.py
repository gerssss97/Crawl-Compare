"""Tests TDD para QtLabeledCombo — foco en theming dual-mode del completer popup.

Bug original: _configure_completer_popup hardcodeaba colores LIGHT, pisando el
stylesheet global con setStyleSheet(). Resultado en dark mode: texto #F1F5F9
(near-white) sobre fondo blanco del sistema -> invisible. Sin border-radius.

Fix: objectName("completerPopup") + WA_TranslucentBackground + reglas
QListView#completerPopup en el stylesheet global (build_qss).
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from PySide6.QtCore import Qt
from UI_qt.widgets.qt_labeled_combo import QtLabeledCombo
from UI_qt.state.observable import StringVar
from UI_qt.styles.stylesheet import build_qss


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def combo(qtbot):
    w = QtLabeledCombo("Hotel", StringVar())
    qtbot.addWidget(w)
    return w


# ---------------------------------------------------------------------------
# Tests — estructura del popup (sin depender de colores renderizados)
# ---------------------------------------------------------------------------

def test_completer_popup_tiene_objectname_correcto(combo):
    """El popup debe tener objectName 'completerPopup' para que el QSS global lo matchee."""
    popup = combo.combo.completer().popup()
    assert popup.objectName() == "completerPopup"


def test_completer_popup_tiene_translucent_background(combo):
    """WA_TranslucentBackground es necesario para que border-radius muestre esquinas
    verdaderamente redondeadas en Windows (sin corners blancos sobre fondo oscuro)."""
    popup = combo.combo.completer().popup()
    assert popup.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


def test_completer_popup_no_tiene_stylesheet_hardcodeado(combo):
    """El popup NO debe tener su propio setStyleSheet. Si lo tiene, pisa el global
    y el theming dual-mode no funciona."""
    popup = combo.combo.completer().popup()
    assert popup.styleSheet() == ""


def test_completer_popup_es_frameless(combo):
    """FramelessWindowHint es necesario para que WA_TranslucentBackground funcione
    y para que el popup no muestre el borde nativo del OS."""
    popup = combo.combo.completer().popup()
    flags = popup.windowFlags()
    assert bool(flags & Qt.WindowType.FramelessWindowHint)


# ---------------------------------------------------------------------------
# Tests — stylesheet global contiene reglas para el popup
# ---------------------------------------------------------------------------

def test_qss_light_contiene_reglas_completer_popup():
    """El QSS de light mode debe incluir QListView#completerPopup."""
    qss = build_qss("light")
    assert "QListView#completerPopup" in qss


def test_qss_dark_contiene_reglas_completer_popup():
    """El QSS de dark mode debe incluir QListView#completerPopup."""
    qss = build_qss("dark")
    assert "QListView#completerPopup" in qss


def test_qss_dark_usa_surface_oscuro_en_popup():
    """En dark mode, el popup debe usar #1E293B (dark surface), no el blanco de light."""
    qss = build_qss("dark")
    # Extraer solo la sección del popup para no hacer match contra otras reglas
    inicio = qss.find("QListView#completerPopup")
    assert inicio != -1
    seccion = qss[inicio: inicio + 400]
    assert "#1E293B" in seccion, "El popup en dark mode debe usar el surface oscuro #1E293B"


def test_qss_dark_no_usa_surface_blanco_en_popup():
    """En dark mode, el popup NO debe usar #FFFFFF (light surface)."""
    qss = build_qss("dark")
    inicio = qss.find("QListView#completerPopup")
    seccion = qss[inicio: inicio + 400]
    assert "#FFFFFF" not in seccion, "El popup en dark mode no debe usar superficie blanca"


def test_qss_dark_define_color_texto_en_popup():
    """En dark mode el popup debe setear color explícito (text_primary = #F1F5F9).
    Sin color explícito, hereda del QWidget global y queda near-white sobre blanco."""
    qss = build_qss("dark")
    inicio = qss.find("QListView#completerPopup")
    seccion = qss[inicio: inicio + 400]
    assert "#F1F5F9" in seccion, "El popup en dark mode debe definir color: #F1F5F9"
