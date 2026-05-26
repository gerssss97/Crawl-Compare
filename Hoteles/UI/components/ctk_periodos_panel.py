"""Panel de periodos de habitacion - version CustomTkinter."""

import customtkinter as ctk
from collections import OrderedDict

from UI.styles import Colors, Typography, Spacing
from .ctk_card import CTkCard
from Models.habitacion_unificada import HabitacionUnificada
from Models.hotelExcel import HabitacionExcel


class CTkPeriodosPanel(CTkCard):
    """Panel que muestra los periodos de una habitacion agrupados por grupo.

    Replica la funcionalidad de PeriodosPanel pero con estetica CustomTkinter.

    Ejemplo de uso:
        panel = CTkPeriodosPanel(parent)
        panel.pack(fill='both', expand=True)

        # Actualizar con datos reales
        panel.actualizar_periodos(habitacion, hotel_excel)
    """

    def __init__(self, parent, **kwargs):
        """Inicializa el panel de periodos.

        Args:
            parent: Widget padre
            **kwargs: Argumentos adicionales para CTkCard
        """
        super().__init__(parent, title="PERIODOS DE LA HABITACION", icon="📅", **kwargs)

    def _setup_ui(self):
        """Construye la estructura base del panel."""
        super()._setup_ui()
        self._mostrar_mensaje("(ninguna seleccionada)")

    def _mostrar_mensaje(self, mensaje, es_advertencia=False):
        """Muestra un mensaje de estado en el panel.

        Args:
            mensaje (str): Mensaje a mostrar
            es_advertencia (bool): Si True, usa color de advertencia
        """
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        color = Colors.WARNING if es_advertencia else Colors.TEXT_DISABLED

        ctk.CTkLabel(
            self.content_frame,
            text=mensaje,
            font=(Typography.FAMILY, Typography.BODY),
            text_color=color,
            wraplength=280,
            justify='center'
        ).pack(expand=True, pady=Spacing.LG)

    def actualizar_periodos(self, habitacion, hotel_excel):
        """Actualiza los periodos mostrados segun la habitacion seleccionada.

        Args:
            habitacion: HabitacionUnificada o HabitacionExcel con periodo_ids
            hotel_excel: Objeto HotelExcel con periodos_group y periodo_por_id()
        """
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Obtener periodo_ids segun el tipo de habitacion
        if isinstance(habitacion, HabitacionUnificada):
            periodo_ids = habitacion.todos_los_periodos()
        elif isinstance(habitacion, HabitacionExcel):
            periodo_ids = habitacion.periodo_ids
        else:
            periodo_ids = getattr(habitacion, 'periodo_ids', set())

        if not periodo_ids:
            self._mostrar_mensaje("Sin periodos asignados", es_advertencia=True)
            return

        # Agrupar periodos por nombre de grupo
        grupos_periodos = OrderedDict()
        for pid in periodo_ids:
            periodo = hotel_excel.periodo_por_id(pid)
            if periodo:
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
            self._mostrar_mensaje("Sin periodos asignados", es_advertencia=True)
            return

        # Scrollable si hay muchos grupos
        if sum(len(p) for p in grupos_periodos.values()) > 4:
            scroll_frame = ctk.CTkScrollableFrame(
                self.content_frame,
                fg_color="transparent",
                scrollbar_button_color=Colors.PRIMARY,
                scrollbar_button_hover_color=Colors.PRIMARY_HOVER
            )
            scroll_frame.pack(fill='both', expand=True)
            self._aislar_scroll(scroll_frame)
            container = scroll_frame
        else:
            container = self.content_frame

        for nombre_grupo, periodos in grupos_periodos.items():
            self._crear_grupo(container, nombre_grupo, periodos)

    def _aislar_scroll(self, scroll_frame):
        root = self.winfo_toplevel()
        _canvas = scroll_frame._parent_canvas

        def _solo_aqui(event):
            widget_bajo_cursor = root.winfo_containing(event.x_root, event.y_root)
            if not self._es_hijo_de(widget_bajo_cursor, scroll_frame):
                return
            _canvas.yview_scroll(int(-event.delta / 6), "units")
            return "break"

        bid = root.bind("<MouseWheel>", _solo_aqui, add="+")
        scroll_frame.bind("<Destroy>", lambda _: root.unbind("<MouseWheel>", bid), add="+")

    def _es_hijo_de(self, widget, contenedor):
        w = widget
        while w is not None:
            if w is contenedor:
                return True
            w = getattr(w, "master", None)
        return False

    def _crear_grupo(self, parent, nombre_grupo, periodos):
        """Crea el bloque visual de un grupo de periodos.

        Args:
            parent: Widget padre
            nombre_grupo (str): Nombre del grupo
            periodos (list): Lista de objetos Periodo del grupo
        """
        grupo_frame = ctk.CTkFrame(
            parent,
            fg_color=Colors.PRIMARY_LIGHT,
            corner_radius=Spacing.RADIUS_MD,
            border_width=1,
            border_color=Colors.BORDER
        )
        grupo_frame.pack(fill='x', pady=(0, Spacing.SM))

        inner = ctk.CTkFrame(grupo_frame, fg_color="transparent")
        inner.pack(fill='both', expand=True, padx=Spacing.SM, pady=Spacing.SM)

        # Titulo del grupo
        ctk.CTkLabel(
            inner,
            text=nombre_grupo,
            font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
            text_color=Colors.TEXT_PRIMARY,
            anchor='w'
        ).pack(fill='x', pady=(0, Spacing.XS))

        # Periodos del grupo
        for periodo in periodos:
            self._crear_periodo_item(inner, periodo)

    def _crear_periodo_item(self, parent, periodo):
        """Crea una fila visual para un periodo individual.

        Args:
            parent: Widget padre
            periodo: Objeto Periodo con fecha_inicio, fecha_fin y nombre
        """
        item_frame = ctk.CTkFrame(
            parent,
            fg_color=Colors.SURFACE,
            corner_radius=Spacing.RADIUS_SM
        )
        item_frame.pack(fill='x', pady=2)

        inicio_str = periodo.fecha_inicio.strftime("%d/%m/%Y")
        fin_str = periodo.fecha_fin.strftime("%d/%m/%Y")

        if periodo.nombre:
            texto = f"  {periodo.nombre}: {inicio_str} - {fin_str}"
        else:
            texto = f"  {inicio_str} - {fin_str}"

        ctk.CTkLabel(
            item_frame,
            text=texto,
            font=(Typography.FAMILY, Typography.SMALL),
            text_color=Colors.TEXT_SECONDARY,
            anchor='w'
        ).pack(fill='x', padx=Spacing.XS, pady=Spacing.XS)

    def limpiar(self):
        """Limpia el panel y muestra estado vacio."""
        self._mostrar_mensaje("(ninguna seleccionada)")

    def reset(self):
        """Resetea el panel (alias de limpiar)."""
        self.limpiar()
