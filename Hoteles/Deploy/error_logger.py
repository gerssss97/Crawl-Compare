"""Logger persistente para .exe: tee de stdout/stderr + excepthook con QMessageBox."""
import sys
import traceback
import datetime
from pathlib import Path


# Flags que identifican mensajes de error — se persisten en el log
_ERROR_FLAGS: frozenset = frozenset({
    "[ERROR]",               # extractor.py — fila inválida
    "[ConfigService] Error", # config_service.py — I/O de config.json
    "[EventBus] Error",      # event_bus.py — listener que explota
    "[historial] Error",     # qt_resultados_modal.py — persistencia historial
    "ERROR en periodo",      # comparador_multiperiodo.py — fallo en un periodo
    "Error:",                # scraper_utils.py — errores de extracción/HTTP
    "Error en intento",      # scraper_utils.py — retry fallido
    "Error decodificando",   # scraper_utils.py — JSON inválido
    "Error procesando",      # scraper_utils.py — habitación inválida
    "Error inesperado",      # scraper_utils.py — catch-all
})

# Flags de mensajes informativos — documentados, NO van al log
# Reservado para futura subcategorización (ej: modo verbose)
_INFO_FLAGS: frozenset = frozenset({
    "[DEBUG]",
    "[PIPELINE]",
    "[startup]",
    "[TESTING MODE]",
    "[EventBus] Emitiendo:",
    "Mejor match para",
    "COMPARACIÓN MULTI-PERIODO",
    "Precio Excel:",
    "MEJOR NOMBRE WEB",
    "COMBO ELEGIDO",
    "→ ",
})


class _TeeStream:
    """Tee completo — todo lo que escribe el stream original va también al log."""
    def __init__(self, original, log_path):
        self._orig = original
        self._log = open(log_path, "a", encoding="utf-8", buffering=1)

    def write(self, text):
        self._orig.write(text)
        self._log.write(text)

    def flush(self):
        self._orig.flush()
        self._log.flush()

    @property
    def encoding(self):
        return self._orig.encoding

    @property
    def errors(self):
        return self._orig.errors


class _FilteredTeeStream:
    """Tee filtrado — solo persiste al log las líneas que matchean _ERROR_FLAGS."""
    def __init__(self, original, log_path):
        self._orig = original
        self._log_path = log_path

    def write(self, text):
        self._orig.write(text)
        if any(flag in text for flag in _ERROR_FLAGS):
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(text)

    def flush(self):
        self._orig.flush()

    @property
    def encoding(self):
        return self._orig.encoding

    @property
    def errors(self):
        return self._orig.errors


class _DummyStream:
    """Stand-in cuando sys.stdout/sys.stderr es None (caso console=False)."""
    def write(self, text):
        pass

    def flush(self):
        pass

    encoding = "utf-8"
    errors = "replace"


def _get_log_dir() -> Path:
    """Carpeta donde se escribe el log: junto al .exe en producción, Hoteles/ en dev."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def setup_error_logging():
    """Instala tee de stdout/stderr + sys.excepthook con QMessageBox. Solo activo en .exe."""
    if not getattr(sys, "frozen", False):
        return

    log_path = _get_log_dir() / f"crawl_compare_{datetime.date.today():%Y%m%d}.log"

    sys.stdout = _FilteredTeeStream(sys.stdout or _DummyStream(), log_path)
    sys.stderr = _TeeStream(sys.stderr or _DummyStream(), log_path)

    def _excepthook(exc_type, exc_value, exc_tb):
        # 1. Persistir el traceback completo al log
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"CRASH {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n")
            f.write(f"{'='*60}\n")
            traceback.print_exception(exc_type, exc_value, exc_tb, file=f)

        # 2. Mostrar diálogo al usuario via Qt si está disponible,
        #    o via Win32 MessageBox nativo como fallback (sin dependencia de Qt).
        #    Importante: NO intentar crear QApplication si ya falló su __init__,
        #    porque un segundo intento puede segfault en Windows.
        _msg = (
            f"Ocurrió un error y la aplicación debe cerrarse.\n\n"
            f"Se guardó un log con los detalles en:\n{log_path}\n\n"
            f"Por favor envía ese archivo para diagnóstico."
        )
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            if QApplication.instance() is not None:
                QMessageBox.critical(None, "Crawl Compare — Error inesperado", _msg)
            else:
                raise RuntimeError("no QApplication")
        except Exception:
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(
                    0, _msg, "Crawl Compare — Error inesperado", 0x10  # MB_ICONERROR
                )
            except Exception:
                pass  # si Win32 también falla, el log al menos está escrito

        # 3. Delegar al excepthook original
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _excepthook
