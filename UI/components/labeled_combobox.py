"""Combobox with label widget."""

import tkinter as tk
from tkinter import ttk
from .base_component import BaseComponent


class LabeledComboBox(BaseComponent):
    """Combobox con label superior estandarizado.

    Componente reutilizable que combina un label y un combobox con
    estilo consistente. Facilita la creación de selectores en formularios.

    Ejemplo de uso:
        combo = LabeledComboBox(
            parent,
            label_text="Selección hotel:",
            textvariable=my_var,
            values=["Hotel A", "Hotel B"],
            fonts=fonts
        )
        combo.pack()
        combo.on_select(lambda value: print(f"Selected: {value}"))
    """

    def __init__(self, parent, label_text="", textvariable=None,
                 values=None, state="readonly", fonts=None, **kwargs):
        """Inicializa el combobox con label.

        Args:
            parent: Widget padre de Tkinter
            label_text (str): Texto del label superior
            textvariable (tk.StringVar, optional): Variable para el valor seleccionado
            values (list, optional): Lista de opciones
            state (str): Estado del combobox ('readonly', 'normal', 'disabled')
            fonts (FontManager, optional): Gestor de fuentes
            **kwargs: Argumentos adicionales para el Frame padre
        """
        self.label_text = label_text
        self.textvariable = textvariable or tk.StringVar()
        self.initial_values = values or []
        self.state = state
        self.fonts = fonts
        self._on_select_callback = None

        super().__init__(parent, **kwargs)

    def _setup_ui(self):
        """Construye la interfaz del componente."""
        bg_color = '#F5F5F5'
        self.configure(bg=bg_color)

        # Label
        font_label = self.fonts.negrita if self.fonts else None
        label = tk.Label(self, text=self.label_text, bg=bg_color, font=font_label)
        label.grid(row=0, column=0, sticky='w', pady=(0, 4))

        # Combobox
        style = ttk.Style()
        font_combo = self.fonts.combo if self.fonts else None
        style.configure('Custom.TCombobox', font=font_combo)

        self._combobox = ttk.Combobox(
            self,
            textvariable=self.textvariable,
            state=self.state,
            style='Custom.TCombobox'
        )
        self._combobox.grid(row=1, column=0, sticky='ew', pady=(0, 10))

        if self.initial_values:
            self._combobox['values'] = self.initial_values

        # Expandir combobox
        self.grid_columnconfigure(0, weight=1)

    def _bind_events(self):
        """Conecta eventos."""
        self._combobox.bind("<<ComboboxSelected>>", self._on_selected)

    def _on_selected(self, event):
        """Maneja el evento de selección."""
        if self._on_select_callback:
            self._on_select_callback(self.textvariable.get())

    def get_value(self):
        """Obtiene el valor seleccionado.

        Returns:
            str: Valor actual del combobox
        """
        return self.textvariable.get()

    def set_value(self, value):
        """Establece el valor seleccionado.

        Args:
            value (str): Valor a seleccionar
        """
        self.textvariable.set(value)

    def set_values(self, values):
        """Actualiza lista de opciones.

        Args:
            values (list): Nueva lista de opciones
        """
        self._combobox['values'] = values

    def get_values(self):
        """Obtiene lista de opciones actual.

        Returns:
            tuple: Tupla de opciones actuales
        """
        return self._combobox['values']

    def reset(self):
        """Resetea la selección."""
        self.textvariable.set("")

    def on_select(self, callback):
        """Registra callback para selección.

        Args:
            callback (callable): Función a llamar cuando se selecciona un item
        """
        self._on_select_callback = callback

    def current(self):
        """Obtiene índice actual seleccionado.

        Returns:
            int: Índice del item seleccionado (-1 si no hay selección)
        """
        return self._combobox.current()

    def set_state(self, state):
        """Cambia el estado del combobox.

        Args:
            state (str): Nuevo estado ('readonly', 'normal', 'disabled')
        """
        self._combobox.config(state=state)
