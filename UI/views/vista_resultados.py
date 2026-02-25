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
        self._text.tag_configure("gap", font=self.fonts.tabla, foreground='#856404', background='#FFF3CD')

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

    def mostrar_resultado_multiperiodo(self, resultado, gap_analysis=None):
        """Muestra resultado multi-periodo intercalando gaps cronológicamente.

        Args:
            resultado: ResultadoComparacionMultiperiodo con breakdown por periodo
            gap_analysis: GapAnalysis opcional con información de gaps
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
        self.agregar(f"{resultado.habitacion_web_matcheada.nombre}\n")

        # Mensaje de matching (justo después de mostrar la habitación web)
        if resultado.mensaje_match:
            self.agregar(f"{resultado.mensaje_match}\n")

        self.agregar("\n")

        # Status global
        if resultado.tiene_discrepancias:
            self.agregar("Estado: ", tags=("bold",))
            self.agregar("❌ DISCREPANCIAS DETECTADAS\n\n", tags=("bold",))
        else:
            self.agregar("Estado: ", tags=("bold",))
            self.agregar("✅ TODO COINCIDE\n\n")

        # Tabla comparativa
        separador = "=" * 90
        self.agregar(f"{separador}\n", tags=("tabla",))
        header = f"{'Rango Fechas':<23} | {'Excel':>12} | {'Web':>12} | {'Estado':<20}\n"
        self.agregar(header, tags=("bold", "tabla"))
        self.agregar(f"{'-' * 90}\n", tags=("tabla",))

        # NUEVO: Mezclar periodos y gaps en orden cronológico
        items = []

        # Agregar periodos
        for res_periodo in resultado.periodos:
            items.append({
                'tipo': 'periodo',
                'fecha_inicio': res_periodo.fecha_inicio_real or res_periodo.periodo.fecha_inicio,
                'fecha_fin': res_periodo.fecha_fin_real or res_periodo.periodo.fecha_fin,
                'data': res_periodo
            })

        # Agregar gaps si existen
        if gap_analysis and gap_analysis.gaps:
            for gap in gap_analysis.gaps:
                items.append({
                    'tipo': 'gap',
                    'fecha_inicio': gap.fecha_inicio,
                    'fecha_fin': gap.fecha_fin,
                    'data': gap
                })

        # Ordenar por fecha de inicio
        items.sort(key=lambda x: x['fecha_inicio'])

        # Mostrar cada item
        for item in items:
            if item['tipo'] == 'periodo':
                # Mostrar fila de periodo
                res_periodo = item['data']
                periodo = res_periodo.periodo

                # Fechas específicas
                if res_periodo.fecha_inicio_real and res_periodo.fecha_fin_real:
                    fecha_inicio_str = res_periodo.fecha_inicio_real.strftime("%d/%m/%Y")
                    fecha_fin_str = res_periodo.fecha_fin_real.strftime("%d/%m/%Y")
                else:
                    fecha_inicio_str = periodo.fecha_inicio.strftime("%d/%m/%Y")
                    fecha_fin_str = periodo.fecha_fin.strftime("%d/%m/%Y")
                fechas_str = f"{fecha_inicio_str} - {fecha_fin_str}"

                # Precios
                if isinstance(res_periodo.precio_excel, (int, float)):
                    precio_excel_str = f"${res_periodo.precio_excel:.2f}"
                else:
                    precio_excel_str = str(res_periodo.precio_excel)[:12]

                precio_web_str = f"${res_periodo.precio_web:.2f}"

                # Estado
                estado_str = "✅ OK" if res_periodo.coincide else "❌ DIFF"

                # Fila
                fila = f"{fechas_str:<23} | {precio_excel_str:>12} | {precio_web_str:>12} | {estado_str:<20}\n"
                tags = ("bold", "tabla") if not res_periodo.coincide else ("tabla",)
                self.agregar(fila, tags=tags)

            elif item['tipo'] == 'gap':
                # Mostrar fila de gap
                gap = item['data']
                fecha_inicio_str = gap.fecha_inicio.strftime("%d/%m/%Y")
                fecha_fin_str = gap.fecha_fin.strftime("%d/%m/%Y")
                fechas_str = f"{fecha_inicio_str} - {fecha_fin_str}"

                # Fila de gap con formato especial
                fila = f"{fechas_str:<23} | {'N/A':>12} | {'N/A':>12} | {'⚠️ SIN COBERTURA':<20}\n"
                self.agregar(fila, tags=("gap",))

        self.agregar(f"{separador}\n\n", tags=("tabla",))

        # Detalles de habitación web
        self.agregar("\nDETALLES HABITACIÓN WEB:\n", tags=("bold",))
        self.agregar(f"🏠 Habitación: {resultado.habitacion_web_matcheada.nombre}\n")

        if resultado.habitacion_web_matcheada.detalles:
            self.agregar(f"📋 Detalles: {resultado.habitacion_web_matcheada.detalles}\n")

        # Mostrar precios web de TODOS los periodos
        self.agregar("\n💵 Precios Web por Periodo:\n", tags=("bold",))
        for res_periodo in resultado.periodos:
            periodo = res_periodo.periodo

            # Formato de fechas
            if res_periodo.fecha_inicio_real and res_periodo.fecha_fin_real:
                fecha_inicio_str = res_periodo.fecha_inicio_real.strftime("%d/%m/%Y")
                fecha_fin_str = res_periodo.fecha_fin_real.strftime("%d/%m/%Y")
            else:
                fecha_inicio_str = periodo.fecha_inicio.strftime("%d/%m/%Y")
                fecha_fin_str = periodo.fecha_fin.strftime("%d/%m/%Y")

            # Mostrar periodo y precio
            self.agregar(f"   • Periodo {periodo.id} ({fecha_inicio_str} - {fecha_fin_str}): ")
            self.agregar(f"${res_periodo.precio_web:.2f}\n", tags=("bold",))

        self.scroll_to_end()
