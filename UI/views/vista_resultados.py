"""Vista de resultados de la comparación."""

import tkinter as tk
from tkinter import ttk


class VistaResultados(tk.Frame):
    """Vista de resultados de la comparación.

    Muestra los resultados de la comparación entre habitación Excel
    y habitación web con formato y scrollbar.

    Ejemplo de uso:
        vista = VistaResultados(parent, fonts)
        vista.pack()
        vista.agregar("Resultado:\n", tags=("bold",))
        vista.agregar("Habitación encontrada")
    """

    def __init__(self, parent, fonts, **kwargs):
        """Inicializa la vista de resultados.

        Args:
            parent: Widget padre de Tkinter
            fonts (FontManager): Gestor de fuentes
            **kwargs: Argumentos adicionales para el Frame
        """
        super().__init__(parent, **kwargs)
        self.fonts = fonts
        self._configurar_ui()

    def _configurar_ui(self):
        """Configura la interfaz de la vista."""
        bg_color = '#F5F5F5'
        self.configure(bg=bg_color)

        # Frame contenedor
        frame_resultado = tk.Frame(self, bg=bg_color)
        frame_resultado.grid(row=0, column=0, sticky='nsew')
        frame_resultado.rowconfigure(0, weight=1)
        frame_resultado.columnconfigure(0, weight=1)

        # Text widget
        self._text = tk.Text(
            frame_resultado,
            height=20,
            width=80,
            font=self.fonts.resultado,
            wrap="word"
        )
        self._text.grid(row=0, column=0, sticky="nsew")

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_resultado, orient="vertical", command=self._text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._text.configure(yscrollcommand=scrollbar.set)

        # Configurar tags de formato
        self._text.tag_configure("bold", font=self.fonts.negrita)
        self._text.tag_configure("grande y negra", font=self.fonts.grande_negrita)

        # Expandir
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def agregar(self, texto, tags=None):
        """Agrega texto al resultado.

        Args:
            texto (str): Texto a agregar
            tags (tuple, optional): Tags de formato a aplicar
        """
        if tags:
            self._text.insert(tk.END, texto, tags)
        else:
            self._text.insert(tk.END, texto)

    def limpiar(self):
        """Limpia todos los resultados."""
        self._text.delete('1.0', tk.END)

    def obtener_widget_text(self):
        """Obtiene widget Text para acceso directo.

        Returns:
            tk.Text: Widget Text interno
        """
        return self._text

    def obtener_texto(self):
        """Obtiene todo el texto de resultados.

        Returns:
            str: Contenido completo de la vista
        """
        return self._text.get('1.0', tk.END)

    def set_readonly(self, readonly=True):
        """Establece el modo readonly.

        Args:
            readonly (bool): True para readonly, False para editable
        """
        if readonly:
            self._text.config(state='disabled')
        else:
            self._text.config(state='normal')

    def scroll_to_end(self):
        """Hace scroll hasta el final del texto."""
        self._text.see(tk.END)
