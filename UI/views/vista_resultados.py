"""Vista de resultados de la comparación."""

import tkinter as tk
from tkinter import ttk
from UI.utils import crear_scrollbar_autohide


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

        # Scrollbar con autohide
        self._scrollbar = ttk.Scrollbar(frame_resultado, orient="vertical", command=self._text.yview)
        self._scrollbar.grid(row=0, column=1, sticky="ns")
        autohide_callback = crear_scrollbar_autohide(self._text, self._scrollbar, layout_manager='grid')
        self._text.configure(yscrollcommand=autohide_callback)

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

    def mostrar_resultado_multiperiodo(self, resultado):
        """Muestra resultado multi-periodo en formato de tabla comparativa.

        Args:
            resultado: ResultadoComparacionMultiperiodo con breakdown por periodo
        """
        self.limpiar()

        # Header
        self.agregar(f"{'='*80}\n", tags=("bold",))
        self.agregar("COMPARACIÓN MULTI-PERIODO\n", tags=("grande y negra",))
        self.agregar(f"{'='*80}\n\n", tags=("bold",))

        # Habitaciones
        self.agregar("Habitación Excel: ", tags=("bold",))
        self.agregar(f"{resultado.habitacion_excel_nombre}\n")

        self.agregar("Habitación Web: ", tags=("bold",))
        self.agregar(f"{resultado.habitacion_web_matcheada.nombre}\n\n")

        # Mensaje de matching
        if resultado.mensaje_match:
            self.agregar(f"{resultado.mensaje_match}\n\n")

        # Status global
        if resultado.tiene_discrepancias:
            self.agregar("Estado: ", tags=("bold",))
            self.agregar("❌ DISCREPANCIAS DETECTADAS\n\n", tags=("bold",))
        else:
            self.agregar("Estado: ", tags=("bold",))
            self.agregar("✅ TODO COINCIDE\n\n")

        # Tabla comparativa
        self.agregar(f"{'='*80}\n")
        header = f"{'Periodo':<25} | {'Fechas':<20} | {'Excel':<10} | {'Web':<10} | {'Estado':<10}\n"
        self.agregar(header, tags=("bold",))
        self.agregar(f"{'-'*80}\n")

        # Filas de periodos
        for idx, res_periodo in enumerate(resultado.periodos, start=1):
            periodo = res_periodo.periodo

            # Nombre del periodo
            nombre_periodo = f"Periodo {periodo.id}"

            # Fechas
            fecha_inicio_str = periodo.fecha_inicio.strftime("%d/%m")
            fecha_fin_str = periodo.fecha_fin.strftime("%d/%m")
            fechas_str = f"{fecha_inicio_str}-{fecha_fin_str}"

            # Precios
            if isinstance(res_periodo.precio_excel, (int, float)):
                precio_excel_str = f"${res_periodo.precio_excel:.2f}"
            else:
                precio_excel_str = str(res_periodo.precio_excel)[:10]

            precio_web_str = f"${res_periodo.precio_web:.2f}"

            # Estado
            estado_str = "✅ OK" if res_periodo.coincide else "❌ DIFF"

            # Fila
            fila = f"{nombre_periodo:<25} | {fechas_str:<20} | {precio_excel_str:<10} | {precio_web_str:<10} | {estado_str:<10}\n"
            self.agregar(fila, tags=("bold",) if not res_periodo.coincide else None)

        self.agregar(f"{'='*80}\n\n")

        # Detalles de habitación web
        from Models.hotelWeb import imprimir_habitacion_web
        texto_habitacion = imprimir_habitacion_web(resultado.habitacion_web_matcheada)
        self.agregar("\nDETALLES HABITACIÓN WEB:\n", tags=("bold",))
        self.agregar(texto_habitacion)

        self.scroll_to_end()
