import sys
import io
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
_qt_app = QApplication.instance() or QApplication(sys.argv)
_trace("QApplication creada")

# Smoke test post-build: si se invoca con --self-test, corre verificaciones
# de bundling y sale (no levanta la UI).
if "--self-test" in sys.argv:
    from Deploy.smoke_test import run_smoke_test
    run_smoke_test()

import Core.gestor_datos  # pre-carga el módulo sin contaminar el namespace
_trace("Core.gestor_datos importado")

from UI_qt.interfaz_qt import MainWindow
_trace("MainWindow importado")


def run_app():
    global _qt_app

    # En .exe mostramos splash y corremos los checks en un QThread worker para
    # que la animación del splash no se congele durante I/O bloqueante.
    if getattr(sys, "frozen", False):
        from Deploy.splash import SplashScreen
        from Deploy.startup_worker import StartupWorker
        from PySide6.QtCore import QEventLoop

        splash = SplashScreen()
        _trace("SplashScreen creado y visible")

        loop = QEventLoop()
        _error_msg = []

        worker = StartupWorker()
        worker.progreso.connect(splash.update_status)
        worker.listo.connect(loop.quit)
        worker.error.connect(lambda msg: (_error_msg.append(msg), loop.quit()))
        worker.start()

        _trace("StartupWorker iniciado, esperando en QEventLoop")
        loop.exec()   # el event loop corre libre: splash anima, worker trabaja
        _trace("QEventLoop terminado")

        splash.close()

        if _error_msg:
            QMessageBox.critical(None, "Error de arranque", _error_msg[0])
            sys.exit(1)
    else:
        # En dev corremos los checks directamente (sin splash, sin worker)
        from Deploy.startup_check import run_checks
        run_checks()

    _trace("instanciando MainWindow")
    window = MainWindow()
    window.show()

    _trace("entrando a Qt event loop")
    sys.exit(_qt_app.exec())


if __name__ == "__main__":
    run_app()
