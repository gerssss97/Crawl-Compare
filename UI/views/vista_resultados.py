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

        # Text widget con altura ajustable
        self._text = tk.Text(
            frame_resultado,
            height=25,
            width=100,
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
        self._text.tag_configure("tabla", font=self.fonts.tabla)
        self._text.tag_configure("rojo", foreground="#CC0000")
        self._text.tag_configure("link", foreground="#0066CC", underline=True)

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

    def _agregar_link(self, url: str):
        """Inserta una URL como hipervínculo clicable."""
        import webbrowser
        tag_name = f"link_{id(url)}_{self._text.index(tk.END)}"
        self._text.tag_configure(tag_name, foreground="#0066CC", underline=True)
        self._text.insert(tk.END, url, (tag_name,))
        self._text.tag_bind(tag_name, "<Button-1>", lambda e, u=url: webbrowser.open(u))
        self._text.tag_bind(tag_name, "<Enter>", lambda e: self._text.config(cursor="hand2"))
        self._text.tag_bind(tag_name, "<Leave>", lambda e: self._text.config(cursor=""))

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
        if resultado.habitacion_web_matcheada:
            self.agregar(f"{resultado.habitacion_web_matcheada.nombre}\n")
        else:
            self.agregar("(no se pudo acceder a la web)\n", tags=("rojo",))

        # Mensaje de matching (justo después de mostrar la habitación web)
        if resultado.mensaje_match:
            self.agregar(f"{resultado.mensaje_match}\n")

        self.agregar("\n")

        # Status global
        alguno_con_error = any(rp.precio_excel == "Error" for rp in resultado.periodos)
        self.agregar("Estado: ", tags=("bold",))
        if alguno_con_error:
            self.agregar("⚠ ERROR al acceder a la web\n\n", tags=("bold", "rojo"))
        elif resultado.tiene_discrepancias:
            self.agregar("❌ DISCREPANCIAS DETECTADAS\n\n", tags=("bold",))
        else:
            self.agregar("✅ TODO COINCIDE\n\n")

        # Tabla comparativa
        separador = "=" * 90
        self.agregar(f"{separador}\n", tags=("tabla",))
        header = f"{'Periodo':<15} | {'Fechas':<13} | {'Excel':>12} | {'Web':>12} | {'Estado':<8}\n"
        self.agregar(header, tags=("bold", "tabla"))
        self.agregar(f"{'-' * 90}\n", tags=("tabla",))

        # Filas de periodos
        for idx, res_periodo in enumerate(resultado.periodos, start=1):
            periodo = res_periodo.periodo

            # Fechas específicas ingresadas (overlap con periodo)
            if res_periodo.fecha_inicio_real and res_periodo.fecha_fin_real:
                fecha_inicio_str = res_periodo.fecha_inicio_real.strftime("%d/%m")
                fecha_fin_str = res_periodo.fecha_fin_real.strftime("%d/%m")
            else:
                # Fallback a fechas del periodo completo
                fecha_inicio_str = periodo.fecha_inicio.strftime("%d/%m")
                fecha_fin_str = periodo.fecha_fin.strftime("%d/%m")
            fechas_str = f"{fecha_inicio_str}-{fecha_fin_str}"

            tiene_error = res_periodo.precio_excel == "Error"

            # Nombre del periodo (nombre si existe, sino fechas; nunca el número)
            nombre_periodo = fechas_str if tiene_error else (periodo.nombre or fechas_str)

            # Precios
            if isinstance(res_periodo.precio_excel, (int, float)):
                precio_excel_str = f"${res_periodo.precio_excel:.2f}"
            else:
                precio_excel_str = str(res_periodo.precio_excel)[:12]

            # Estado y precio web
            if tiene_error:
                estado_str = "⚠ ERROR"
                precio_web_str = "---"
            elif res_periodo.coincide:
                estado_str = "✅ OK"
                precio_web_str = f"${res_periodo.precio_web:.2f}"
            else:
                estado_str = "❌ DIFF"
                precio_web_str = f"${res_periodo.precio_web:.2f}"

            # Fila con alineación: periodo y fechas a izq, precios a derecha, estado a izq
            fila = f"{nombre_periodo:<15} | {fechas_str:<13} | {precio_excel_str:>12} | {precio_web_str:>12} | {estado_str:<8}\n"
            tags = ("bold", "tabla") if not res_periodo.coincide else ("tabla",)
            self.agregar(fila, tags=tags)

        self.agregar(f"{separador}\n\n", tags=("tabla",))

        # Detalles de errores de scraping (si los hay)
        periodos_con_error = [rp for rp in resultado.periodos if rp.precio_excel == "Error"]
        if periodos_con_error:
            self.agregar("ERRORES DE ACCESO WEB:\n", tags=("bold",))
            for rp in periodos_con_error:
                periodo = rp.periodo
                if rp.fecha_inicio_real and rp.fecha_fin_real:
                    fecha_inicio_str = rp.fecha_inicio_real.strftime("%d/%m/%Y")
                    fecha_fin_str = rp.fecha_fin_real.strftime("%d/%m/%Y")
                else:
                    fecha_inicio_str = periodo.fecha_inicio.strftime("%d/%m/%Y")
                    fecha_fin_str = periodo.fecha_fin.strftime("%d/%m/%Y")

                self.agregar(f"  {fecha_inicio_str} - {fecha_fin_str}:\n", tags=("bold",))
                if rp.error_url:
                    self.agregar("    URL:   ")
                    self._agregar_link(rp.error_url)
                    self.agregar("\n")
                if rp.error_msg:
                    self.agregar(f"    Error: {rp.error_msg}\n")
            self.agregar("\n")

        # Detalles de habitación web
        if resultado.habitacion_web_matcheada:
            self.agregar("DETALLES HABITACION WEB:\n", tags=("bold",))
            self.agregar(f"  Habitacion: {resultado.habitacion_web_matcheada.nombre}\n")

            if resultado.habitacion_web_matcheada.detalles:
                self.agregar(f"  Detalles: {resultado.habitacion_web_matcheada.detalles}\n")

        # Mostrar precios web de periodos que NO fallaron
        periodos_ok = [rp for rp in resultado.periodos if rp.precio_excel != "Error"]
        if periodos_ok:
            self.agregar("\n  Precios Web por Periodo:\n", tags=("bold",))
            for res_periodo in periodos_ok:
                periodo = res_periodo.periodo

                # Formato de fechas
                if res_periodo.fecha_inicio_real and res_periodo.fecha_fin_real:
                    fecha_inicio_str = res_periodo.fecha_inicio_real.strftime("%d/%m/%Y")
                    fecha_fin_str = res_periodo.fecha_fin_real.strftime("%d/%m/%Y")
                else:
                    fecha_inicio_str = periodo.fecha_inicio.strftime("%d/%m/%Y")
                    fecha_fin_str = periodo.fecha_fin.strftime("%d/%m/%Y")

                # Mostrar periodo y precio (nombre si existe, sino solo fechas)
                etiqueta = periodo.nombre if periodo.nombre else f"{fecha_inicio_str} - {fecha_fin_str}"
                self.agregar(f"    {etiqueta}: ")
                self.agregar(f"${res_periodo.precio_web:.2f}\n", tags=("bold",))

        self.scroll_to_end()
