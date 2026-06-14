"""Mini test visual de Fase 0: abre la ventana del spike y la deja abierta para probar el resize a mano.

A diferencia de spike_resize.py (que mide y se auto-cierra), este queda abierto: arrastra
los bordes para sentir la fluidez del resize en vivo. Reutiliza la ventana y el QSS del spike.

Correr con el Python del env crawler:
    "C:/Users/German Lucero/anaconda3/envs/crawler/python.exe" Hoteles/UI_qt/spike_visual.py
"""
import sys
import os

base = r'C:\Users\German Lucero\ProyectosChino\Crawl-Compare'
hoteles_dir = os.path.join(base, 'Hoteles')
sys.path.insert(0, base)
sys.path.insert(0, hoteles_dir)
os.chdir(hoteles_dir)

from PySide6.QtWidgets import QApplication
from UI_qt.spike_resize import SpikeWindow, build_qss


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(build_qss())
    win = SpikeWindow()
    win.setWindowTitle("Spike PySide6 - Probá el resize (arrastrá los bordes)")
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
