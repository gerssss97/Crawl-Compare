"""Centralized font management for the application."""

from tkinter import font


class FontManager:
    """Gestor centralizado de fuentes de la aplicación.

    Consolida todas las definiciones de fuentes en un solo lugar,
    facilitando cambios globales de estilo y manteniendo consistencia visual.

    Todas las fuentes están basadas en Helvetica con diferentes tamaños y pesos.
    """

    def __init__(self, root):
        """Inicializa todas las fuentes de la aplicación.

        Args:
            root: Ventana raíz de Tkinter (necesaria para crear fuentes)
        """
        # Fuente normal para labels y texto general
        self.normal = font.Font(family="Helvetica", size=12)

        # Fuente en negrita para labels importantes
        self.negrita = font.Font(family="Helvetica", size=12, weight="bold")

        # Fuente grande y en negrita para títulos principales
        self.grande_negrita = font.Font(family="Helvetica", size=16, weight="bold")

        # Fuente para el área de resultados
        self.resultado = font.Font(family="Helvetica", size=12, weight="normal")

        # Fuente para títulos de periodos
        self.periodos_titulo = font.Font(family="Helvetica", size=11, weight="bold")

        # Fuente para contenido de periodos
        self.periodos_contenido = font.Font(family="Helvetica", size=11)

        # Fuente destacada para el precio
        self.precio = font.Font(family="Helvetica", size=14, weight="bold")

        # Fuente para comboboxes (mismo tamaño que normal)
        self.combobox = font.Font(family="Helvetica", size=12)

        # Fuente grande para el texto dentro de comboboxes
        self.combo = font.Font(family="Helvetica", size=20)

        # Fuente para botones
        self.boton = font.Font(family="Helvetica", size=13, weight="bold")

    def get_font(self, font_name):
        """Obtiene una fuente por nombre.

        Args:
            font_name (str): Nombre de la fuente a obtener

        Returns:
            Font: Objeto Font de Tkinter

        Raises:
            AttributeError: Si el nombre de fuente no existe
        """
        return getattr(self, font_name)
