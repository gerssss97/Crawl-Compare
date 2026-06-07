"""Logger persistente para .exe: tee de stdout/stderr + excepthook con messagebox."""
import sys
import traceback
import datetime
from pathlib import Path


class _TeeStream:
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
    """Instala tee de stdout/stderr + sys.excepthook con messagebox. Solo activo en .exe."""
    if not getattr(sys, "frozen", False):
        return  # En dev no tocamos nada

    log_path = _get_log_dir() / f"crawl_compare_{datetime.date.today():%Y%m%d}.log"

    # Los flags ya vienen forzados por el override de debug_config.py.
    # Acá solo envolvemos stdout/stderr para que los print() vayan al log también.
    sys.stdout = _TeeStream(sys.stdout or _DummyStream(), log_path)
    sys.stderr = _TeeStream(sys.stderr or _DummyStream(), log_path)

    def _excepthook(exc_type, exc_value, exc_tb):
        # 1. Persistir el traceback completo al log
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"CRASH {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n")
            f.write(f"{'='*60}\n")
            traceback.print_exception(exc_type, exc_value, exc_tb, file=f)

        # 2. Avisar al usuario con un messagebox simple (tk puro, sin CTk)
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Crawl Compare — Error inesperado",
                f"Ocurrió un error y la aplicación debe cerrarse.\n\n"
                f"Se guardó un log con los detalles en:\n{log_path}\n\n"
                f"Por favor envía ese archivo para diagnóstico."
            )
            root.destroy()
        except Exception:
            pass  # Si el messagebox falla, al menos el log ya está escrito

        # 3. Delegar al excepthook original (consola si existe)
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _excepthook
