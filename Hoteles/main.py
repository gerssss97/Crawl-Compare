import sys
import io
import os
import time
from datetime import datetime

# Forzar UTF-8 en stdout/stderr — necesario en .exe de PyInstaller en Windows
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

_T0 = time.perf_counter()
def _trace(etapa: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    elapsed_ms = int((time.perf_counter() - _T0) * 1000)
    try:
        print(f"[startup {ts}] (+{elapsed_ms:>5}ms) {etapa}", flush=True)
    except Exception:
        pass

_trace("UTF-8 wrappers instalados")

from Deploy.error_logger import setup_error_logging
setup_error_logging()
_trace("error_logger setup completo")

# QApplication debe existir antes de cualquier widget Qt (incluido el splash).
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtCore import Qt, QSize
from UI_qt.styles.constants import APP_WIN_ICON_PX, APP_WIN_ICON_PAD_PX
_qt_app = QApplication.instance() or QApplication(sys.argv)
_app_icon_path = os.path.join(os.path.dirname(__file__), "UI_qt", "assets", "app_icon.ico")
if os.path.exists(_app_icon_path):
    _src = QIcon(_app_icon_path).pixmap(QSize(APP_WIN_ICON_PX, APP_WIN_ICON_PX))
    _padded = QPixmap(QSize(APP_WIN_ICON_PX + APP_WIN_ICON_PAD_PX, APP_WIN_ICON_PX))
    _padded.fill(Qt.transparent)
    _p = QPainter(_padded)
    _p.drawPixmap(0, 0, _src)
    _p.end()
    _qt_app.setWindowIcon(QIcon(_padded))
_trace("QApplication creada")

# Smoke test post-build: si se invoca con --self-test, corre verificaciones
# de bundling y sale (no levanta la UI).
if "--self-test" in sys.argv:
    from Deploy.smoke_test import run_smoke_test
    run_smoke_test()

def run_app():
    global _qt_app
    _splash = None

    if getattr(sys, "frozen", False):
        from Deploy.splash import SplashScreen
        from Deploy.startup_worker import StartupWorker
        from PySide6.QtCore import QEventLoop

        _splash = SplashScreen()
        _trace("SplashScreen creado y visible")

        loop = QEventLoop()
        _error_msg = []

        worker = StartupWorker()
        worker.progreso.connect(_splash.update_status)
        worker.listo.connect(loop.quit)
        worker.error.connect(lambda msg: (_error_msg.append(msg), loop.quit()))
        worker.start()

        _trace("StartupWorker iniciado, esperando en QEventLoop")
        loop.exec()   # el event loop corre libre: splash anima, worker trabaja
        _trace("QEventLoop terminado")

        if _error_msg:
            _splash.close()
            QMessageBox.critical(None, "Error de arranque", _error_msg[0])
            sys.exit(1)

        _splash.update_status("Cargando interfaz...")
    else:
        from Deploy.startup_check import run_checks
        run_checks()

    # Imports pesados: el splash sigue visible mientras esto carga (solo en .exe)
    import Core.gestor_datos  # noqa: F401
    _trace("Core.gestor_datos importado")

    from UI_qt.interfaz_qt import MainWindow
    _trace("MainWindow importado")

    if _splash:
        _splash.close()

    _trace("instanciando MainWindow")
    window = MainWindow()
    window.show()

    _trace("entrando a Qt event loop")
    sys.exit(_qt_app.exec())


if __name__ == "__main__":
    run_app()
