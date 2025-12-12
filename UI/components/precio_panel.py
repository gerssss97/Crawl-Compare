"""Panel for displaying room price."""

import tkinter as tk
from tkinter import ttk
from .base_component import BaseComponent


class PrecioPanel(BaseComponent):
    """Panel de visualización del precio de habitación.

    Componente que muestra el precio de una habitación seleccionada
    con formato visual destacado.

    Ejemplo de uso:
        panel = PrecioPanel(parent, textvariable=precio_var, fonts=fonts)
        panel.pack()
        # El precio se actualiza automáticamente cuando cambia precio_var
    """

    def __init__(self, parent, textvariable=None, fonts=None, **kwargs):
        """Inicializa el panel de precio.

        Args:
            parent: Widget padre de Tkinter
            textvariable (tk.StringVar, optional): Variable del precio
            fonts (FontManager, optional): Gestor de fuentes
            **kwargs: Argumentos adicionales para el Frame padre
        """
        self.textvariable = textvariable or tk.StringVar(value="(ninguna seleccionada)")
        self.fonts = fonts
        super().__init__(parent, **kwargs)

    def _setup_ui(self):
        """Construye la interfaz del componente."""
        # Título
        font_titulo = self.fonts.negrita if self.fonts else None
        ttk.Label(self, text="Precio de la habitación", font=font_titulo).grid(
            row=0, column=0, sticky='w', pady=(0, 5), padx=(0, 10))

        # Contenedor del precio
        precio_container = tk.Frame(self, relief=tk.SOLID, borderwidth=1, bg='#F5F5F5')
        precio_container.grid(row=1, column=0, sticky='ew', pady=(0, 15), padx=(0, 10))

        # Label del precio
        font_precio = self.fonts.precio if self.fonts else None
        self._label_precio = tk.Label(
            precio_container,
            textvariable=self.textvariable,
            font=font_precio,
            bg='#F5F5F5',
            fg='#2C3E50',
            padx=12,
            pady=8,
            anchor='w'
        )
        self._label_precio.pack(fill='both', expand=True)

    def get_value(self):
        """Obtiene el precio actual.

        Returns:
            str: Precio actual como string
        """
        return self.textvariable.get()

    def set_value(self, precio):
        """Establece el precio.

        Args:
            precio (str): Nuevo precio a mostrar
        """
        self.textvariable.set(precio)

    def reset(self):
        """Resetea el precio al valor por defecto."""
        self.textvariable.set("(ninguna seleccionada)")
