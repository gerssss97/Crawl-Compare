import sys, os, time
sys.path.insert(0, r"C:\Users\German\Gerssss\IA\Hoteles\Hoteles")
sys.path.insert(0, r"C:\Users\German\Gerssss\IA\Hoteles")
os.chdir(r"C:\Users\German\Gerssss\IA\Hoteles\Hoteles")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
app = QApplication.instance() or QApplication(sys.argv)

from UI_qt.interfaz_qt import MainWindow
from UI_qt.widgets.qt_labeled_combo import QtLabeledCombo
win = MainWindow(theme="dark")
win.show()

from PIL import ImageGrab
import threading

def interact():
    time.sleep(3.5)

    # Poblar el primer combo (Hotel) y abrir el popup
    combos = win.findChildren(QtLabeledCombo)
    if combos:
        hotel_combo = combos[0]
        hotel_combo.set_values(["Alvear Palace", "Faena Hotel Buenos Aires", "Four Seasons Buenos Aires"])
        time.sleep(0.3)
        hotel_combo.combo._open_completer()
        time.sleep(1.2)

    win.raise_()
    win.activateWindow()

    img = ImageGrab.grab()
    img.save(r"C:\Users\German\Gerssss\IA\Hoteles\.claude\skills\scripts\app_qt_screenshot.png")
    print("SCREENSHOT_OK", flush=True)
    app.quit()

t = threading.Thread(target=interact, daemon=True)
t.start()
app.exec()
