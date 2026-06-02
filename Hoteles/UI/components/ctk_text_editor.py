"""CTkTextEditor — CTkTextbox con shortcuts de teclado ya configurados."""

import tkinter as tk

import customtkinter as ctk

from UI.styles import Colors, Typography


class CTkTextEditor(ctk.CTkTextbox):
    """CTkTextbox con shortcuts de edición estándar bakeados.

    Shortcuts incluidos:
        Ctrl+Backspace  borrar palabra anterior
        Ctrl+Delete     borrar palabra siguiente
        Ctrl+Z          deshacer
        Ctrl+Y          rehacer
        Ctrl+A          seleccionar todo

    Args:
        parent:               widget padre
        lines:                si se pasa, fija el alto en función de N renglones.
        auto_grow:            si True, el alto crece con el contenido.
        autocomplete_options: lista de strings para el inline suggester. Si None, no se activa.
        trigger_char:         carácter que dispara el suggester (default "{").
        close_char:           carácter que se agrega al completar (default "}").
        n:                    mínimo de letras después del trigger para mostrar sugerencias.
        **kwargs:             resto de kwargs se pasan directo a CTkTextbox.
    """

    def __init__(
        self,
        parent,
        lines: int | None = None,
        auto_grow: bool = False,
        autocomplete_options: list[str] | None = None,
        trigger_char: str = "{",
        close_char: str = "}",
        n: int = 1,
        context_resolver=None,
        **kwargs,
    ):
        font_arg = kwargs.get("font", (Typography.FAMILY, Typography.BODY))
        self._font_size = font_arg[1] if isinstance(font_arg, tuple) else Typography.BODY
        self._min_lines = lines or 10

        if lines is not None:
            kwargs["height"] = lines * (self._font_size + 6)

        kwargs.setdefault("wrap", "word")
        kwargs.setdefault("font", (Typography.FAMILY, Typography.BODY))
        kwargs.setdefault("fg_color", Colors.BACKGROUND)
        kwargs.setdefault("text_color", Colors.TEXT_PRIMARY)
        kwargs.setdefault("corner_radius", 0)
        kwargs.setdefault("border_width", 0)

        super().__init__(parent, **kwargs)
        self._bind_shortcuts(self._textbox)

        if auto_grow:
            self._setup_auto_grow()

        if autocomplete_options is not None:
            from UI.components.ctk_inline_suggester import CTkInlineSuggester
            self._suggester = CTkInlineSuggester(
                text_widget=self._textbox,
                options=autocomplete_options,
                trigger_char=trigger_char,
                close_char=close_char,
                n=n,
                context_resolver=context_resolver,
            )
            self._suggester.attach()

    def _setup_auto_grow(self):
        line_h = self._font_size + 6
        min_h  = self._min_lines * line_h

        def _recalcular(_=None):
            lineas = int(self._textbox.index(tk.END).split(".")[0]) - 1
            self.configure(height=max(min_h, lineas * line_h))

        self._textbox.bind("<KeyRelease>", _recalcular, add="+")
        self.after(100, _recalcular)

    # ── API pública ────────────────────────────────────────────────────────

    def get_value(self) -> str:
        return self.get("1.0", tk.END).strip()

    def set_value(self, text: str):
        self.delete("1.0", tk.END)
        self.insert("1.0", text)

    # ── Shortcuts ─────────────────────────────────────────────────────────

    def _bind_shortcuts(self, widget: tk.Text):
        def borrar_palabra_anterior(_):
            pos = widget.index(tk.INSERT)
            inicio = widget.index(f"{pos} wordstart")
            if inicio == pos:
                inicio = widget.index(f"{pos}-1c wordstart")
            widget.delete(inicio, pos)
            return "break"

        def borrar_palabra_siguiente(_):
            pos = widget.index(tk.INSERT)
            fin = widget.index(f"{pos} wordend")
            widget.delete(pos, fin)
            return "break"

        def deshacer(_):
            try:
                widget.edit_undo()
            except Exception:
                pass
            return "break"

        def rehacer(_):
            try:
                widget.edit_redo()
            except Exception:
                pass
            return "break"

        def seleccionar_todo(_):
            widget.tag_add(tk.SEL, "1.0", tk.END)
            widget.mark_set(tk.INSERT, tk.END)
            return "break"

        widget.bind("<Control-BackSpace>", borrar_palabra_anterior)
        widget.bind("<Control-Delete>",    borrar_palabra_siguiente)
        widget.bind("<Control-z>",         deshacer)
        widget.bind("<Control-y>",         rehacer)
        widget.bind("<Control-a>",         seleccionar_todo)
