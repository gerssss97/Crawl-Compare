import sys, os, time
sys.path.insert(0, r"C:\Users\German\Gerssss\IA\Hoteles\Hoteles")
sys.path.insert(0, r"C:\Users\German\Gerssss\IA\Hoteles")
os.chdir(r"C:\Users\German\Gerssss\IA\Hoteles\Hoteles")

from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)

from UI_qt.interfaz_qt import MainWindow
win = MainWindow()
win.show()

from PIL import ImageGrab
import threading

def capture():
    time.sleep(4)
    sx, sy = win.pos().x(), win.pos().y()
    img = ImageGrab.grab(bbox=(sx, sy, sx + win.width(), sy + win.height()))
    img.save(r"C:\Users\German\Gerssss\IA\Hoteles\.claude\skills\scripts\app_qt_screenshot.png")
    print("SCREENSHOT_OK", flush=True)
    os._exit(0)

t = threading.Thread(target=capture, daemon=True)
t.start()
app.exec()
