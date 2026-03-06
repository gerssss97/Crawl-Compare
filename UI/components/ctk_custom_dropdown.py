"""Dropdown personalizado que funciona correctamente con CTk."""

import customtkinter as ctk
from UI.styles import Colors, Typography, Spacing


class CTkCustomDropdown(ctk.CTkFrame):
    """Dropdown personalizado que realmente llena el ancho y es clickeable.

    Solución workaround para las limitaciones de CTkComboBox:
    - Llena 100% del ancho del dropdown
    - Se puede clickear en cualquier parte para abrir
    - No permite editar el texto
    """

    def __init__(self, parent, values=None, textvariable=None, command=None, placeholder_text="Seleccionar...", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.values = values or []
        self.textvariable = textvariable
        self.command = command
        self._placeholder_text = placeholder_text
        self._dropdown_open = False
        self._dropdown_window = None

        # Frame principal con entrada y botón
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="x")

        # Frame que simula un entry (sin canvas interno que cause redibujados)
        self.entry = ctk.CTkFrame(
            self.main_frame,
            fg_color=Colors.SURFACE,
            border_color=Colors.BORDER,
            corner_radius=Spacing.RADIUS_MD,
            border_width=1,
            cursor="hand2",
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, Spacing.SM))

        self._display_label = ctk.CTkLabel(
            self.entry,
            text=placeholder_text,
            font=(Typography.FAMILY, Typography.BODY),
            text_color=Colors.TEXT_DISABLED,
            fg_color="transparent",
            anchor="w",
            height=36,
        )
        self._display_label.pack(fill="x", padx=Spacing.SM, pady=2)

        # Botón dropdown
        self.button = ctk.CTkButton(
            self.main_frame,
            text="▼",
            width=40,
            height=40,
            fg_color=Colors.BORDER,
            hover_color=Colors.PRIMARY,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=Spacing.RADIUS_MD,
            command=self._on_button_click,
        )
        self.button.pack(side="right", padx=(Spacing.SM, 0))

        self.entry.bind("<Button-1>", lambda _: self._toggle_dropdown(), add="+")
        self._display_label.bind("<Button-1>", lambda _: self._toggle_dropdown(), add="+")

        # Sincronizar el entry cuando la StringVar cambia externamente
        if self.textvariable:
            self.textvariable.trace_add("write", self._on_textvariable_changed)

    def _on_button_click(self):
        self._toggle_dropdown()

    def _on_textvariable_changed(self, *args):
        value = self.textvariable.get()
        self._set_display(value)

    def _set_display(self, value):
        """Actualiza el label de display con el valor o el placeholder."""
        if value:
            self._display_label.configure(text=value, text_color=Colors.TEXT_PRIMARY)
        else:
            self._display_label.configure(text=self._placeholder_text, text_color=Colors.TEXT_DISABLED)

    def _toggle_dropdown(self):
        if self._dropdown_open:
            self._close_dropdown()
        else:
            self._open_dropdown()

    def _open_dropdown(self):
        if self._dropdown_open:
            return

        self._dropdown_open = True
        self.update_idletasks()

        # Coordenadas absolutas de pantalla para posicionar el Toplevel
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 2

        # winfo_width() devuelve píxeles reales ya escalados por CTk.
        # CTkToplevel geometry() también aplica scaling, así que dividimos
        # para compensar y que el ancho final coincida exactamente con el widget.
        scaling = self._get_widget_scaling()
        width_ctk = int(self.winfo_width() / scaling)

        self._dropdown_window = ctk.CTkToplevel(self)
        self._dropdown_window.wm_overrideredirect(True)
        self._dropdown_window.configure(fg_color=Colors.SURFACE)
        self._dropdown_window.geometry(f"{width_ctk}x300+{x}+{y}")

        scroll_frame = ctk.CTkScrollableFrame(
            self._dropdown_window,
            fg_color=Colors.SURFACE,
            scrollbar_button_color=Colors.BORDER,
            scrollbar_button_hover_color=Colors.PRIMARY,
        )
        scroll_frame.pack(fill="both", expand=True)

        for value in self.values:
            btn = ctk.CTkButton(
                scroll_frame,
                text=value,
                fg_color="transparent",
                hover_color=Colors.PRIMARY_LIGHT,
                text_color=Colors.TEXT_PRIMARY,
                anchor="w",
                command=lambda v=value: self._select_option(v),
            )
            btn.pack(fill="x", pady=2)

        # Cerrar al hacer click fuera del dropdown (no con FocusOut, que se dispara
        # inmediatamente cuando el botón roba el foco cerrando el dropdown al instante)
        self.winfo_toplevel().bind("<Button-1>", self._on_click_outside, add="+")

    def _on_click_outside(self, event):
        """Cierra el dropdown si el click fue fuera de la ventana del dropdown."""
        if self._dropdown_window is None:
            return
        # Verificar si el click fue dentro de la ventana del dropdown
        win = self._dropdown_window
        wx, wy = win.winfo_rootx(), win.winfo_rooty()
        ww, wh = win.winfo_width(), win.winfo_height()
        if not (wx <= event.x_root <= wx + ww and wy <= event.y_root <= wy + wh):
            self._close_dropdown()

    def _close_dropdown(self):
        self.winfo_toplevel().unbind("<Button-1>")
        if self._dropdown_window:
            self._dropdown_window.destroy()
            self._dropdown_window = None
        self._dropdown_open = False

    def _select_option(self, value):
        self._close_dropdown()
        if self.textvariable:
            self.textvariable.set(value)  # dispara _on_textvariable_changed → _set_display
        else:
            self._set_display(value)
        if self.command:
            self.command(value)

    def set_values(self, values):
        self.values = values

    def get(self):
        text = self._display_label.cget("text")
        return "" if text == self._placeholder_text else text

    def set(self, value):
        self._set_display(value)
        if self.textvariable:
            self.textvariable.set(value)

    def configure(self, **kwargs):
        if "command" in kwargs:
            self.command = kwargs.pop("command")
        if "values" in kwargs:
            self.set_values(kwargs.pop("values"))
        if kwargs:
            super().configure(**kwargs)
