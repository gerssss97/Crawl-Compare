"""Entry widget con label (para campos numéricos y de texto)."""

import tkinter as tk
from tkinter import ttk
from .base_component import BaseComponent


class EntradaEtiquetada(BaseComponent):
    """Entry con label superior estandarizado.

    Componente reutilizable que combina un label y un entry con
    estilo consistente. Útil para formularios.

    Ejemplo de uso:
        entrada = EntradaEtiquetada(
            parent,
            texto_label="Cantidad de adultos:",
            textvariable=adultos_var,
            width=10,
            fonts=fonts
        )
        entrada.pack()
    """

    def __init__(self, parent, texto_label="", textvariable=None,
                 width=None, validate=None, validatecommand=None,
                 fonts=None, **kwargs):
        """Inicializa el entry con label.

        Args:
            parent: Widget padre de Tkinter
            texto_label (str): Texto del label superior
            textvariable (tk.Variable, optional): Variable para el valor
            width (int, optional): Ancho del entry
            validate (str, optional): Tipo de validación ('key', 'focusout', etc.)
            validatecommand (tuple, optional): Comando de validación
            fonts (FontManager, optional): Gestor de fuentes
            **kwargs: Argumentos adicionales para el Frame padre
        """
        self.texto_label = texto_label
        self.textvariable = textvariable or tk.StringVar()
        self.width = width
        self.validate = validate
        self.validatecommand = validatecommand
        self.fonts = fonts

        super().__init__(parent, **kwargs)

    def _setup_ui(self):
        """Construye la interfaz del componente."""
        bg_color = '#F5F5F5'
        self.configure(bg=bg_color)

        # Label
        font_label = self.fonts.normal if self.fonts else None
        label = tk.Label(self, text=self.texto_label, bg=bg_color, font=font_label)
        label.grid(row=0, column=0, sticky='w', pady=(0, 4))

        # Entry
        entry_kwargs = {
            'textvariable': self.textvariable
        }

        if self.width:
            entry_kwargs['width'] = self.width
        if self.validate:
            entry_kwargs['validate'] = self.validate
        if self.validatecommand:
            entry_kwargs['validatecommand'] = self.validatecommand

        self._entry = ttk.Entry(self, **entry_kwargs)
        self._entry.grid(row=1, column=0, sticky='ew', pady=(0, 10))

        # Expandir entry
        self.grid_columnconfigure(0, weight=1)

    def get_value(self):
        """Obtiene el valor del entry.

        Returns:
            str o int/float: Valor actual (depende del tipo de textvariable)
        """
        return self.textvariable.get()

    def set_value(self, value):
        """Establece el valor del entry.

        Args:
            value: Valor a establecer
        """
        self.textvariable.set(value)

    def reset(self):
        """Resetea el entry."""
        if isinstance(self.textvariable, tk.IntVar):
            self.textvariable.set(0)
        elif isinstance(self.textvariable, tk.DoubleVar):
            self.textvariable.set(0.0)
        else:
            self.textvariable.set("")

    def set_state(self, state):
        """Cambia el estado del entry.

        Args:
            state (str): Nuevo estado ('normal', 'readonly', 'disabled')
        """
        self._entry.config(state=state)

    def focus(self):
        """Pone el foco en el entry."""
        self._entry.focus()
