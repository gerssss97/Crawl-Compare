"""CTkInlineSuggester — popup de sugerencias inline para tk.Text."""

import tkinter as tk
from typing import Callable

from UI.styles import Colors, Typography


class CTkInlineSuggester:
    """Popup de autocomplete que se activa al escribir después de un trigger_char.

    Args:
        text_widget:      el tk.Text (interno) sobre el que se bindean los eventos.
        options:          lista de strings a sugerir (fallback cuando no hay context_resolver).
        trigger_char:     carácter que abre el contexto de sugerencia (default "{").
        close_char:       carácter que se agrega al completar (default "}").
        n:                mínimo de letras después del trigger para mostrar el popup.
        context_resolver: callable opcional — recibe el texto desde el inicio hasta el cursor
                          y retorna la lista de opciones correcta para ese contexto.
                          Si es None, se usan siempre `options`.
    """

    _BG         = "#1E293B"
    _FG         = "#F1F5F9"
    _SELECT_BG  = "#3B82F6"
    _SELECT_FG  = "#FFFFFF"
    _BORDER     = "#334155"
    _FONT       = (Typography.FAMILY, 12)

    def __init__(
        self,
        text_widget: tk.Text,
        options: list[str],
        trigger_char: str = "{",
        close_char: str = "}",
        n: int = 1,
        context_resolver: Callable[[str], list[str]] | None = None,
    ):
        self._tw               = text_widget
        self._options          = options
        self._trigger          = trigger_char
        self._close            = close_char
        self._n                = n
        self._context_resolver = context_resolver
        self._popup: tk.Toplevel | None = None
        self._listbox: tk.Listbox | None = None
        self._filtered: list[str] = []
        self._active           = False

    # ── API pública ────────────────────────────────────────────────────────

    def attach(self):
        self._tw.bind("<KeyRelease>", self._on_key_release, add="+")
        self._tw.bind("<FocusOut>",   self._cerrar,         add="+")

    def detach(self):
        self._tw.unbind("<KeyRelease>")
        self._tw.unbind("<FocusOut>")
        self._cerrar()

    # ── Detección del contexto ─────────────────────────────────────────────

    def _obtener_prefijo(self) -> str | None:
        """Devuelve el texto entre el último trigger_char sin cerrar y el cursor.

        Retorna None si el cursor no está dentro de un contexto abierto.
        """
        pos    = self._tw.index(tk.INSERT)
        linea  = int(pos.split(".")[0])
        col    = int(pos.split(".")[1])
        texto  = self._tw.get(f"{linea}.0", pos)

        # Busca el último trigger sin close intermedio
        ultima = texto.rfind(self._trigger)
        if ultima == -1:
            return None

        entre = texto[ultima + 1:]
        if self._close in entre:
            return None

        return entre

    # ── Lógica de sugerencias ──────────────────────────────────────────────

    def _on_key_release(self, event: tk.Event):
        # Teclas de navegación: delegar al listbox si el popup está abierto
        if self._active:
            if event.keysym == "Escape":
                self._cerrar()
                return
            if event.keysym in ("Up", "Down", "Return", "Tab"):
                return  # ya manejadas en _bind_popup_keys

        prefijo = self._obtener_prefijo()

        if prefijo is None or len(prefijo) < self._n:
            self._cerrar()
            return

        if self._context_resolver is not None:
            texto_hasta_cursor = self._tw.get("1.0", tk.INSERT)
            opciones_activas = self._context_resolver(texto_hasta_cursor)
        else:
            opciones_activas = self._options

        self._filtered = [
            o for o in opciones_activas
            if o.lower().startswith(prefijo.lower())
        ]

        if not self._filtered:
            self._cerrar()
            return

        self._mostrar(prefijo)

    def _mostrar(self, prefijo: str):
        # Posición del cursor en pantalla
        try:
            bbox = self._tw.bbox(tk.INSERT)
        except tk.TclError:
            return
        if not bbox:
            return

        x = self._tw.winfo_rootx() + bbox[0]
        y = self._tw.winfo_rooty() + bbox[1] + bbox[3] + 2

        if self._popup is None:
            self._crear_popup()

        # Actualiza items
        self._listbox.delete(0, tk.END)
        for item in self._filtered:
            self._listbox.insert(tk.END, f"  {self._trigger}{item}{self._close}  ")

        self._listbox.selection_set(0)
        self._listbox.activate(0)

        # Ajusta alto al número de items (máx 6 visibles)
        visible = min(len(self._filtered), 6)
        self._listbox.configure(height=visible)

        self._popup.geometry(f"+{x}+{y}")
        self._popup.deiconify()
        self._popup.lift()
        self._active = True

    def _crear_popup(self):
        self._popup = tk.Toplevel(self._tw)
        self._popup.overrideredirect(True)
        self._popup.wm_attributes("-topmost", True)
        self._popup.configure(bg=self._BORDER)

        frame = tk.Frame(self._popup, bg=self._BORDER, padx=1, pady=1)
        frame.pack(fill="both", expand=True)

        self._listbox = tk.Listbox(
            frame,
            font=self._FONT,
            bg=self._BG,
            fg=self._FG,
            selectbackground=self._SELECT_BG,
            selectforeground=self._SELECT_FG,
            activestyle="none",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            exportselection=False,
            cursor="hand2",
        )
        self._listbox.pack(fill="both", expand=True)
        self._listbox.bind("<ButtonRelease-1>", self._confirmar_click)

        self._bind_popup_keys()

    def _bind_popup_keys(self):
        for widget in (self._tw, self._listbox):
            widget.bind("<Up>",    self._mover_arriba,  add="+")
            widget.bind("<Down>",  self._mover_abajo,   add="+")
            widget.bind("<Tab>",   self._confirmar_key, add="+")
            widget.bind("<Return>", self._confirmar_key, add="+")

    # ── Navegación ─────────────────────────────────────────────────────────

    def _mover_arriba(self, _=None):
        if not self._active:
            return
        sel = self._listbox.curselection()
        idx = sel[0] if sel else 0
        nuevo = max(0, idx - 1)
        self._listbox.selection_clear(0, tk.END)
        self._listbox.selection_set(nuevo)
        self._listbox.activate(nuevo)
        self._listbox.see(nuevo)
        return "break"

    def _mover_abajo(self, _=None):
        if not self._active:
            return
        sel = self._listbox.curselection()
        idx = sel[0] if sel else -1
        nuevo = min(len(self._filtered) - 1, idx + 1)
        self._listbox.selection_clear(0, tk.END)
        self._listbox.selection_set(nuevo)
        self._listbox.activate(nuevo)
        self._listbox.see(nuevo)
        return "break"

    # ── Confirmación ───────────────────────────────────────────────────────

    def _confirmar_key(self, _=None):
        if not self._active:
            return
        sel = self._listbox.curselection()
        if not sel:
            return "break"
        self._insertar(self._filtered[sel[0]])
        return "break"

    def _confirmar_click(self, event: tk.Event):
        idx = self._listbox.nearest(event.y)
        if 0 <= idx < len(self._filtered):
            self._insertar(self._filtered[idx])

    def _insertar(self, tag: str):
        pos     = self._tw.index(tk.INSERT)
        linea   = int(pos.split(".")[0])
        col     = int(pos.split(".")[1])
        texto   = self._tw.get(f"{linea}.0", pos)

        inicio_col = texto.rfind(self._trigger)
        inicio_idx = f"{linea}.{inicio_col}"

        self._tw.delete(inicio_idx, pos)
        self._tw.insert(inicio_idx, f"{self._trigger}{tag}{self._close}")
        self._cerrar()

    # ── Cierre ─────────────────────────────────────────────────────────────

    def _cerrar(self, _=None):
        self._active = False
        if self._popup:
            self._popup.withdraw()
