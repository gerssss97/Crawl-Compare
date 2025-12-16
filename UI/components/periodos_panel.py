"""Panel for displaying room periods."""

import tkinter as tk
from tkinter import ttk
from collections import OrderedDict
from .base_component import BaseComponent
from Models.habitacion_unificada import HabitacionUnificada
from Models.hotelExcel import HabitacionExcel
from UI.utils import crear_scrollbar_autohide


class PeriodosPanel(BaseComponent):
    """Panel de visualización de periodos de habitación.

    Componente que muestra los periodos asociados a una habitación
    agrupados por grupo de periodo, con formato visual mejorado.

    Ejemplo de uso:
        panel = PeriodosPanel(parent, fonts=fonts)
        panel.pack()
        panel.actualizar_periodos(habitacion, hotel_excel)
    """

    def __init__(self, parent, fonts=None, **kwargs):
        """Inicializa el panel de periodos.

        Args:
            parent: Widget padre de Tkinter
            fonts (FontManager, optional): Gestor de fuentes
            **kwargs: Argumentos adicionales para el Frame padre
        """
        self.fonts = fonts
        super().__init__(parent, **kwargs)

    def _setup_ui(self):
        """Construye la interfaz del componente."""
        # Label título
        font_titulo = self.fonts.negrita if self.fonts else None
        ttk.Label(self, text="Periodos de la habitación", font=font_titulo).grid(
            row=0, column=0, sticky='w', pady=(10, 5), padx=(0, 10))

        # Frame contenedor con borde y altura fija
        container = tk.Frame(self, relief=tk.SOLID, borderwidth=1, bg='#F5F5F5', height=300)
        container.grid(row=1, column=0, sticky='nsew', pady=(0, 10), padx=(0, 10))
        container.grid_propagate(False)  # Mantener altura fija

        # Text widget sin especificar altura ni ancho (se adaptará al container)
        font_contenido = self.fonts.periodos_contenido if self.fonts else None
        self._text = tk.Text(
            container,
            wrap="word",
            font=font_contenido,
            bg='#FAFAFA',
            relief=tk.FLAT,
            padx=10,
            pady=10,
            cursor='arrow'
        )
        self._text.grid(row=0, column=0, sticky="nsew")

        # Scrollbar con autohide
        self._scrollbar = ttk.Scrollbar(container, orient="vertical", command=self._text.yview)
        self._scrollbar.grid(row=0, column=1, sticky="ns")
        autohide_callback = crear_scrollbar_autohide(self._text, self._scrollbar, layout_manager='grid')
        self._text.configure(yscrollcommand=autohide_callback)

        # Configurar como readonly
        self._text.config(state='disabled')

        # Configurar tags
        font_titulo_periodo = self.fonts.periodos_titulo if self.fonts else None
        font_normal = self.fonts.normal if self.fonts else None

        self._text.tag_configure("advertencia", foreground="#C0392B",
                                font=font_normal)
        self._text.tag_configure("grupo", foreground="#34495E",
                                font=font_titulo_periodo, spacing1=6, spacing3=3)
        self._text.tag_configure("periodo", foreground="#555555",
                                font=font_contenido, lmargin1=20, lmargin2=20)

        # Configurar expansión
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

    def get_value(self):
        """Obtiene el contenido del panel.

        Returns:
            str: Texto actual del panel
        """
        return self._text.get('1.0', tk.END)

    def set_value(self, value):
        """Establece el contenido del panel.

        Args:
            value (str): Texto a mostrar
        """
        self._text.config(state='normal')
        self._text.delete('1.0', tk.END)
        self._text.insert(tk.END, value)
        self._text.config(state='disabled')

    def actualizar_periodos(self, habitacion, hotel_excel):
        """Actualiza periodos de una habitación.

        Args:
            habitacion: HabitacionUnificada o HabitacionExcel con periodo_ids
            hotel_excel: Objeto HotelExcel con periodos_group
        """
        self._text.config(state='normal')
        self._text.delete('1.0', tk.END)

        # Obtener todos los periodo_ids según el tipo de habitación
        if isinstance(habitacion, HabitacionUnificada):
            # Si es unificada, obtener TODOS los periodos de TODAS las variantes
            periodo_ids = habitacion.todos_los_periodos()
        elif isinstance(habitacion, HabitacionExcel):
            # Si es una habitación simple, usar sus periodo_ids
            periodo_ids = habitacion.periodo_ids
        else:
            # Fallback: intentar acceder al atributo periodo_ids
            periodo_ids = getattr(habitacion, 'periodo_ids', set())

        # Verificar si hay periodos
        if not periodo_ids:
            self._text.insert(tk.END, "⚠️ ADVERTENCIA:\n", "advertencia")
            self._text.insert(tk.END, "Sin periodos asignados", "advertencia")
            self._text.config(state='disabled')
            return

        # Agrupar periodos por grupo
        grupos_periodos = OrderedDict()

        for pid in periodo_ids:
            periodo = hotel_excel.periodo_por_id(pid)
            if periodo:
                # Buscar grupo
                nombre_grupo = None
                for grupo in hotel_excel.periodos_group:
                    if periodo in grupo.periodos:
                        nombre_grupo = grupo.nombre
                        break

                if nombre_grupo:
                    if nombre_grupo not in grupos_periodos:
                        grupos_periodos[nombre_grupo] = []
                    grupos_periodos[nombre_grupo].append(periodo)

        if not grupos_periodos:
            self._text.insert(tk.END, "⚠️ ADVERTENCIA:\n", "advertencia")
            self._text.insert(tk.END, "Sin periodos asignados", "advertencia")
            self._text.config(state='disabled')
            return

        # Insertar con formato
        for i, (nombre_grupo, periodos) in enumerate(grupos_periodos.items()):
            if i > 0:
                self._text.insert(tk.END, "\n")

            # Nombre del grupo
            self._text.insert(tk.END, f"{nombre_grupo}\n", "grupo")

            # Periodos
            for periodo in periodos:
                inicio_str = periodo.fecha_inicio.strftime("%d/%m/%Y")
                fin_str = periodo.fecha_fin.strftime("%d/%m/%Y")

                if periodo.nombresito:
                    self._text.insert(tk.END,
                        f"  • {periodo.nombresito}: {inicio_str} - {fin_str}\n",
                        "periodo")
                else:
                    self._text.insert(tk.END,
                        f"  • {inicio_str} - {fin_str}\n",
                        "periodo")

        self._text.config(state='disabled')

    def limpiar(self):
        """Limpia el panel."""
        self._text.config(state='normal')
        self._text.delete('1.0', tk.END)
        self._text.config(state='disabled')

    def reset(self):
        """Resetea el panel (alias de limpiar)."""
        self.limpiar()
