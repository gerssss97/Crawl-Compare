"""Splash screen de arranque del .exe: ventana tk pura con label de estado y barra indeterminada."""
import tkinter as tk
from tkinter import ttk


# Colores hardcodeados: el splash corre antes de inicializar CTk,
# así que no podemos importar UI/styles/colors.py (depende de CTk).
_BG = "#F8FAFC"
_TITLE_FG = "#1E293B"
_SUBTITLE_FG = "#64748B"
_BAR_COLOR = "#2563EB"

_WIDTH = 400
_HEIGHT = 200


class SplashScreen:
    def __init__(self):
        self._root = tk.Tk()
        self._root.overrideredirect(True)  # sin barra de título
        self._root.attributes("-topmost", True)
        self._root.configure(bg=_BG)

        # Centrado en pantalla
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        x = (screen_w - _WIDTH) // 2
        y = (screen_h - _HEIGHT) // 2
        self._root.geometry(f"{_WIDTH}x{_HEIGHT}+{x}+{y}")

        # Título
        tk.Label(
            self._root,
            text="Crawl Compare",
            font=("Segoe UI", 18, "bold"),
            fg=_TITLE_FG,
            bg=_BG,
        ).pack(pady=(28, 4))

        # Subtítulo
        tk.Label(
            self._root,
            text="Comparador de Precios de Hoteles",
            font=("Segoe UI", 10),
            fg=_SUBTITLE_FG,
            bg=_BG,
        ).pack(pady=(0, 24))

        # Estado dinámico
        self._status_var = tk.StringVar(value="Iniciando...")
        tk.Label(
            self._root,
            textvariable=self._status_var,
            font=("Segoe UI", 10),
            fg=_TITLE_FG,
            bg=_BG,
        ).pack(pady=(0, 12))

        # Barra de progreso indeterminada
        style = ttk.Style(self._root)
        try:
            style.theme_use("default")
        except tk.TclError:
            pass
        style.configure(
            "Splash.Horizontal.TProgressbar",
            background=_BAR_COLOR,
            troughcolor=_BG,
            bordercolor=_BG,
            lightcolor=_BAR_COLOR,
            darkcolor=_BAR_COLOR,
        )
        self._bar = ttk.Progressbar(
            self._root,
            mode="indeterminate",
            length=320,
            style="Splash.Horizontal.TProgressbar",
        )
        self._bar.pack()
        self._bar.start(12)

        self._root.update()

    def update_status(self, mensaje: str) -> None:
        """Actualiza el label de estado y fuerza redibujado sin mainloop.
        Además imprime a stdout con prefijo [startup] para que quede en el
        log persistente y en la consola si está visible."""
        self._status_var.set(mensaje)
        try:
            print(f"[startup] {mensaje}", flush=True)
        except Exception:
            pass
        self._root.update()

    def close(self) -> None:
        """Para la barra y destruye el root para liberar el slot de Tk."""
        try:
            self._bar.stop()
        except tk.TclError:
            pass
        try:
            self._root.destroy()
        except tk.TclError:
            pass
