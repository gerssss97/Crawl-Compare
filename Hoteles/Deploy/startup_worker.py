"""Worker QThread para correr run_checks() sin bloquear el hilo principal.

El splash anima libremente en el event loop de Qt mientras este thread
hace I/O (carga de .env, verificación de Playwright). Cuando termina emite
`listo` para que main.py cierre el splash y abra la ventana principal.
Si algo falla emite `error` con el mensaje y main.py muestra el diálogo.
"""
from PySide6.QtCore import QThread, Signal


class StartupWorker(QThread):
    progreso = Signal(str)   # mensaje para el splash
    listo    = Signal()      # todos los checks pasaron
    error    = Signal(str)   # mensaje de error (la app debe salir)

    def run(self):
        try:
            from Deploy.startup_check import check_env, check_playwright

            self.progreso.emit("Verificando configuración...")
            check_env()

            self.progreso.emit("Verificando navegador...")
            check_playwright()

            self.listo.emit()
        except SystemExit:
            # check_env / check_playwright llaman sys.exit(1) si algo falla.
            # Lo capturamos para emitir el signal de error en vez de matar el proceso.
            self.error.emit("Error en la verificación de arranque. Revisá los logs.")
        except Exception as e:
            self.error.emit(str(e))
