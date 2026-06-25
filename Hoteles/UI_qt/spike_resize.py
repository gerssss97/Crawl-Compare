"""Spike de Fase 0: prototipo PySide6 que reproduce el layout 2-columnas y mide el resize.

Reproduce la estructura real de interfaz_ctk.py (header + panel izq form 65% + panel
der precio/periodos 35%) en PySide6, estilado con QSS generado desde Colors/Spacing
(las MISMAS constantes que usa la UI actual). Luego simula un drag del borde con
resize() consecutivos y cronometra el re-layout, replicando el método de
.claude/skills/scripts/resize_probe.py para comparar contra los ~1000ms de CTk.

Correr con el Python del env crawler:
    "C:/Users/German Lucero/anaconda3/envs/crawler/python.exe" Hoteles/UI_qt/spike_resize.py
"""
import sys
import os
import time

base = r'C:\Users\German Lucero\ProyectosChino\Crawl-Compare'
hoteles_dir = os.path.join(base, 'Hoteles')
sys.path.insert(0, base)
sys.path.insert(0, hoteles_dir)
os.chdir(hoteles_dir)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame,
    QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit,
)
from PySide6.QtCore import Qt, QTimer

from UI_qt.styles import Colors, Spacing


def build_qss() -> str:
    """Genera el QSS global desde las constantes actuales (fuente unica de verdad)."""
    return f"""
    QMainWindow, QWidget {{
        background-color: {Colors.BACKGROUND};
        color: {Colors.TEXT_PRIMARY};
        font-family: "Segoe UI";
        font-size: 13px;
    }}

    /* Header */
    QFrame#header {{
        background-color: {Colors.HEADER_BG};
        border: none;
    }}
    QLabel#headerTitle {{
        color: {Colors.HEADER_TEXT};
        font-size: 18px;
        font-weight: bold;
    }}

    /* Cards */
    QFrame#card {{
        background-color: {Colors.SURFACE};
        border: 1px solid {Colors.BORDER};
        border-radius: {Spacing.RADIUS_MD}px;
    }}
    QLabel#cardTitle {{
        color: {Colors.TEXT_PRIMARY};
        font-size: 13px;
        font-weight: bold;
    }}
    QLabel#fieldLabel {{
        color: {Colors.TEXT_PRIMARY};
        font-weight: bold;
    }}

    /* Inputs */
    QLineEdit, QComboBox {{
        background-color: {Colors.SURFACE};
        border: 1px solid {Colors.BORDER};
        border-radius: {Spacing.RADIUS_SM}px;
        padding: 6px 10px;
        min-height: 24px;
    }}
    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {Colors.PRIMARY};
    }}
    QComboBox::drop-down {{ border: none; width: 28px; }}
    QComboBox QAbstractItemView {{
        background-color: {Colors.SURFACE};
        selection-background-color: {Colors.PRIMARY};
        selection-color: {Colors.HEADER_TEXT};
        border: 1px solid {Colors.BORDER};
        outline: none;
    }}

    /* Boton primario */
    QPushButton#btnPrimary {{
        background-color: {Colors.PRIMARY};
        color: {Colors.HEADER_TEXT};
        border: none;
        border-radius: {Spacing.RADIUS_MD}px;
        min-height: 44px;
        font-weight: bold;
    }}
    QPushButton#btnPrimary:hover {{ background-color: {Colors.PRIMARY_HOVER}; }}

    /* Panel derecho (precio/periodos) */
    QFrame#pricePanel, QFrame#periodsPanel {{
        background-color: {Colors.SURFACE};
        border: 1px solid {Colors.BORDER};
        border-radius: {Spacing.RADIUS_MD}px;
    }}
    QLabel#priceValue {{
        color: {Colors.PRIMARY};
        font-size: 28px;
        font-weight: bold;
    }}
    QTextEdit {{
        background-color: {Colors.SURFACE};
        border: 1px solid {Colors.BORDER};
        border-radius: {Spacing.RADIUS_SM}px;
    }}
    """


def _card(title: str) -> QFrame:
    card = QFrame()
    card.setObjectName("card")
    lay = QVBoxLayout(card)
    lay.setContentsMargins(Spacing.CARD_PADDING, Spacing.CARD_PADDING,
                           Spacing.CARD_PADDING, Spacing.CARD_PADDING)
    lay.setSpacing(Spacing.FORM_GAP)
    t = QLabel(title)
    t.setObjectName("cardTitle")
    lay.addWidget(t)
    return card, lay


def _field(label_text: str, widget: QWidget) -> QWidget:
    box = QWidget()
    v = QVBoxLayout(box)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(Spacing.XXS)
    lbl = QLabel(label_text)
    lbl.setObjectName("fieldLabel")
    v.addWidget(lbl)
    v.addWidget(widget)
    return box


class SpikeWindow(QMainWindow):
    """Reproduce el layout 2-columnas de interfaz_ctk.py con widgets dummy."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spike PySide6 - Resize")
        self.resize(1200, 760)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(56)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(Spacing.LG, 0, Spacing.LG, 0)
        title = QLabel("Comparador de Precios de Hoteles")
        title.setObjectName("headerTitle")
        hl.addWidget(title)
        hl.addStretch()
        root.addWidget(header)

        # Cuerpo 2 columnas
        body = QWidget()
        bl = QHBoxLayout(body)
        bl.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        bl.setSpacing(Spacing.LG)
        bl.addWidget(self._build_left(), stretch=65)
        bl.addWidget(self._build_right(), stretch=35)
        root.addWidget(body, stretch=1)

    def _build_left(self) -> QWidget:
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(Spacing.MD)

        # Card seleccion de reserva
        card1, l1 = _card("SELECCION DE RESERVA")
        combo_hotel = QComboBox()
        combo_hotel.addItems(["Hotel Serene", "Hotel Aurora", "Hotel Luminous"])
        l1.addWidget(_field("Hotel", combo_hotel))
        combo_hab = QComboBox()
        combo_hab.addItems(["Suite Doble", "Habitacion Standard", "Suite Premium"])
        l1.addWidget(_field("Habitacion", combo_hab))
        v.addWidget(card1)

        # Card fechas
        card2, l2 = _card("FECHAS Y HUESPEDES")
        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(Spacing.MD)
        rl.addWidget(_field("Fecha entrada", QLineEdit("01/01/2026")))
        rl.addWidget(_field("Fecha salida", QLineEdit("05/01/2026")))
        rl.addWidget(_field("Adultos", QLineEdit("2")))
        rl.addWidget(_field("Ninos", QLineEdit("0")))
        l2.addWidget(row)
        v.addWidget(card2)

        # Boton
        btn = QPushButton("Ejecutar Comparacion")
        btn.setObjectName("btnPrimary")
        v.addWidget(btn)
        v.addStretch()
        return wrap

    def _build_right(self) -> QWidget:
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(Spacing.MD)

        # Panel precio
        price = QFrame()
        price.setObjectName("pricePanel")
        pl = QVBoxLayout(price)
        pl.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        pt = QLabel("PRECIO")
        pt.setObjectName("cardTitle")
        pl.addWidget(pt)
        val = QLabel("$ 45.000")
        val.setObjectName("priceValue")
        pl.addWidget(val)
        pl.addStretch()
        v.addWidget(price, stretch=1)

        # Panel periodos
        periods = QFrame()
        periods.setObjectName("periodsPanel")
        pel = QVBoxLayout(periods)
        pel.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        pet = QLabel("PERIODOS")
        pet.setObjectName("cardTitle")
        pel.addWidget(pet)
        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setPlainText("Temporada Alta: $45.000\nTemporada Media: $38.000\nTemporada Baja: $30.000")
        pel.addWidget(txt)
        v.addWidget(periods, stretch=1)
        return wrap


def run_probe(win: QMainWindow, app: QApplication):
    """Simula un drag del borde derecho y cronometra el re-layout (mismo metodo que resize_probe.py)."""
    app.processEvents()

    base_h = win.height()
    widths = list(range(1000, 1400, 25)) + list(range(1400, 1000, -25))

    tiempos = []
    for w in widths:
        win.resize(w, base_h)
        t0 = time.perf_counter()
        app.processEvents()      # aca Qt resuelve el layout + repintado
        dt = (time.perf_counter() - t0) * 1000
        tiempos.append(dt)

    n = len(tiempos)
    avg = sum(tiempos) / n
    peor = max(tiempos)
    over16 = sum(1 for t in tiempos if t > 16)
    print(f"[spike-qt] frames={n}  avg={avg:.1f}ms  peor={peor:.1f}ms  frames>16ms={over16}/{n}")
    print(f"[spike-qt] baseline CTk: avg ~1000ms, peor ~2000ms")
    veredicto = "OK: resize fluido (GATE <100ms)" if peor < 100 else "LENTO: revisar"
    print(f"[spike-qt] {veredicto}")

    app.quit()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(build_qss())
    win = SpikeWindow()
    win.show()
    QTimer.singleShot(800, lambda: run_probe(win, app))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
