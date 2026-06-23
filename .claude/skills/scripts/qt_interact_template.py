"""
Template base para scripts de interacción Qt (debugging visual Tipo B).

Uso:
  1. Copiar este archivo a qt_interact_{descripcion_corta}.py
  2. Reemplazar la sección SCENARIO con las acciones específicas del bug
  3. Ejecutar: conda run -n crawler python .claude/skills/scripts/qt_interact_{descripcion}.py
  4. Leer los screenshots generados en este mismo directorio
  5. Borrar el script una vez resuelto el bug
"""

import sys, os, time, threading

sys.path.insert(0, r"C:\Users\German\Gerssss\IA\Hoteles\Hoteles")
sys.path.insert(0, r"C:\Users\German\Gerssss\IA\Hoteles")
os.chdir(r"C:\Users\German\Gerssss\IA\Hoteles\Hoteles")

from PySide6.QtWidgets import QApplication, QPushButton, QComboBox, QTabWidget, QWidget
from PySide6.QtCore import QTimer

app = QApplication.instance() or QApplication(sys.argv)

from UI_qt.interfaz_qt import MainWindow
win = MainWindow()
win.show()
win.raise_()
win.activateWindow()

from PIL import ImageGrab

SCRIPTS_DIR = r"C:\Users\German\Gerssss\IA\Hoteles\.claude\skills\scripts"


def screenshot(name: str):
    sx, sy = win.pos().x(), win.pos().y()
    img = ImageGrab.grab(bbox=(sx, sy, sx + win.width(), sy + win.height()))
    path = os.path.join(SCRIPTS_DIR, name)
    img.save(path)
    print(f"SCREENSHOT_OK: {path}", flush=True)


def find_button(text: str):
    return next((b for b in win.findChildren(QPushButton) if b.text() == text), None)


def scenario():
    time.sleep(3)  # render inicial

    # ── PASO 1: estado inicial ──────────────────────────────────────────────
    screenshot("step_01_inicial.png")

    # ── PASO 2: interacciones (REEMPLAZAR ESTO) ─────────────────────────────
    #
    # Ejemplos:
    #
    # Click en botón por texto:
    #   btn = find_button("Ejecutar Comparación")
    #   if btn: btn.click()
    #   time.sleep(1)
    #
    # Cambiar opción de dropdown:
    #   combos = win.findChildren(QComboBox)
    #   if combos: combos[0].setCurrentIndex(1)
    #   time.sleep(0.5)
    #
    # Cambiar tab activa:
    #   tabs = win.findChildren(QTabWidget)
    #   if tabs: tabs[0].setCurrentIndex(1)
    #   time.sleep(0.5)
    #
    # ── PASO 3: estado final ────────────────────────────────────────────────
    screenshot("step_02_final.png")

    app.quit()


t = threading.Thread(target=scenario, daemon=True)
t.start()
app.exec()
