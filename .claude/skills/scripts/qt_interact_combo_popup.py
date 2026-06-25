"""
Verifica:
1. Popup del click en input (completer) vs popup de la flechita (nativo)
2. Scroll en el completer popup sin scrollbar visible
"""
import sys, os, time
sys.path.insert(0, r"C:\Users\German\Gerssss\IA\Hoteles\Hoteles")
sys.path.insert(0, r"C:\Users\German\Gerssss\IA\Hoteles")
os.chdir(r"C:\Users\German\Gerssss\IA\Hoteles\Hoteles")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtCore import QPoint, QPointF
app = QApplication.instance() or QApplication(sys.argv)

from UI_qt.interfaz_qt import MainWindow
from UI_qt.widgets.qt_labeled_combo import QtLabeledCombo
win = MainWindow(theme="light")
win.show()

from PIL import ImageGrab
import threading

SHOTS_DIR = r"C:\Users\German\Gerssss\IA\Hoteles\.claude\skills\scripts"
HOTELES = [
    "Alvear Palace",
    "Faena Hotel Buenos Aires",
    "Four Seasons Buenos Aires",
    "Hilton Buenos Aires",
    "Sofitel Buenos Aires Arroyo",
    "NH Collection Buenos Aires Lancaster",
]

def screenshot(name):
    img = ImageGrab.grab()
    path = os.path.join(SHOTS_DIR, name)
    img.save(path)
    print(f"SCREENSHOT_OK: {name}", flush=True)

def interact():
    time.sleep(3.5)

    combos = win.findChildren(QtLabeledCombo)
    if not combos:
        print("ERROR: no QtLabeledCombo found", flush=True)
        app.quit()
        return

    hotel_combo = combos[0]
    hotel_combo.set_values(HOTELES)
    time.sleep(0.3)

    win.raise_()
    win.activateWindow()

    # --- Step 1: popup del CLICK EN INPUT (completer) ---
    hotel_combo._open_completer_popup()
    time.sleep(1.0)
    screenshot("step_01_completer_popup.png")

    # --- Step 2: intentar scrollear en el completer popup ---
    popup = hotel_combo._completer.popup()
    sb = popup.verticalScrollBar()
    pos_antes = sb.value()

    # Simular wheel event hacia abajo
    wheel = QWheelEvent(
        QPointF(popup.rect().center()),
        QPointF(popup.mapToGlobal(popup.rect().center())),
        QPoint(0, -120),   # delta negativo = scroll down
        QPoint(0, -120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False
    )
    app.sendEvent(popup.viewport(), wheel)
    time.sleep(0.3)
    pos_despues = sb.value()
    print(f"Scroll test — antes: {pos_antes}, despues: {pos_despues}, scrolleo: {pos_antes != pos_despues}", flush=True)
    screenshot("step_02_despues_scroll.png")

    # Cerrar el completer popup
    popup.hide()
    time.sleep(0.5)

    # --- Step 3: popup de la FLECHITA (nativo) ---
    hotel_combo.combo.showPopup()
    time.sleep(1.0)
    win.raise_()
    win.activateWindow()
    screenshot("step_03_native_popup.png")

    hotel_combo.combo.hidePopup()
    time.sleep(0.3)
    app.quit()

t = threading.Thread(target=interact, daemon=True)
t.start()
app.exec()
