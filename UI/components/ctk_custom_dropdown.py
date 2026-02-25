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

    def __init__(self, parent, values=None, textvariable=None, command=None, **kwargs):
        """Inicializa el dropdown personalizado.

        Args:
            parent: Widget padre
            values (list): Opciones del dropdown
            textvariable (tk.StringVar): Variable para el valor seleccionado
            command (callable): Función a ejecutar al seleccionar
            **kwargs: Argumentos adicionales para CTkFrame
        """
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.values = values or []
        self.textvariable = textvariable
        self.command = command
        self._dropdown_open = False
        self._dropdown_window = None

        # Frame principal con entrada y botón
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="x")

        # Entry (no editable)
        self.entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Seleccionar...",
            font=(Typography.FAMILY, Typography.BODY),
            fg_color=Colors.SURFACE,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_DISABLED,
            corner_radius=Spacing.RADIUS_MD,
            border_width=1,
            height=40,
        )
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.configure(state="readonly")  # No editable

        # Botón dropdown
        self.button = ctk.CTkButton(
            main_frame,
            text="▼",
            width=40,
            height=40,
            fg_color=Colors.BORDER,
            hover_color=Colors.PRIMARY,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=Spacing.RADIUS_MD,
            command=self._toggle_dropdown,
        )
        self.button.pack(side="right", padx=(Spacing.SM, 0))

        # Bindear click en el entry para abrir dropdown
        self.entry.bind("<Button-1>", lambda e: self._toggle_dropdown())

    def _toggle_dropdown(self):
        """Abre o cierra el dropdown."""
        if self._dropdown_open:
            self._close_dropdown()
        else:
            self._open_dropdown()

    def _open_dropdown(self):
        """Abre el dropdown desplegable."""
        if self._dropdown_open:
            return

        self._dropdown_open = True

        # Crear ventana toplevel para el dropdown
        self._dropdown_window = ctk.CTkToplevel(self)
        self._dropdown_window.wm_overrideredirect(True)
        self._dropdown_window.configure(fg_color=Colors.SURFACE)

        # Posicionar debajo del entry
        self.entry.update_idletasks()
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height() + 2
        width = self.entry.winfo_width()

        self._dropdown_window.geometry(f"{width}x300+{x}+{y}")

        # Scrollable frame con opciones - sin bordes
        scroll_frame = ctk.CTkScrollableFrame(
            self._dropdown_window,
            fg_color=Colors.SURFACE,
            scrollbar_button_color=Colors.BORDER,
            scrollbar_button_hover_color=Colors.PRIMARY,
        )
        scroll_frame.pack(fill="both", expand=True)

        # Crear botones para cada opción
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
            # Sin padx para que no desborde - pady para separación vertical
            btn.pack(fill="x", pady=2)

        # Bindear click fuera para cerrar
        self._dropdown_window.bind("<FocusOut>", lambda e: self._close_dropdown())
        self._dropdown_window.focus()

    def _close_dropdown(self):
        """Cierra el dropdown."""
        if self._dropdown_window:
            self._dropdown_window.destroy()
            self._dropdown_window = None
        self._dropdown_open = False

    def _select_option(self, value):
        """Selecciona una opción."""
        if self.textvariable:
            self.textvariable.set(value)
        self.entry.delete(0, "end")
        self.entry.insert(0, value)
        self._close_dropdown()
        if self.command:
            self.command(value)

    def set_values(self, values):
        """Actualiza los valores del dropdown."""
        self.values = values

    def get(self):
        """Obtiene el valor actual."""
        return self.entry.get()

    def set(self, value):
        """Establece el valor."""
        self.entry.delete(0, "end")
        self.entry.insert(0, value)
        if self.textvariable:
            self.textvariable.set(value)

    def configure(self, **kwargs):
        """Configura propiedades del dropdown.

        Soporta:
            - command: callable a ejecutar al seleccionar
            - values: lista de opciones
        """
        if "command" in kwargs:
            self.command = kwargs.pop("command")
        if "values" in kwargs:
            self.set_values(kwargs.pop("values"))
        # Pasar el resto a CTkFrame si las hay
        if kwargs:
            super().configure(**kwargs)
