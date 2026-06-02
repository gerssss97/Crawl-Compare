"""Panel de precio - versión CustomTkinter con diseño mejorado."""

import customtkinter as ctk
from UI.styles import Colors, Typography, Spacing
from UI.styles.icons import Icons
from .ctk_card import CTkCard


class CTkPrecioPanel(CTkCard):
    """Panel que muestra precios con diseño visual atractivo.
    
    Soporta dos modos:
    1. Mensaje simple (cuando no hay precio)
    2. Múltiples precios por periodo (con gradientes y diseño moderno)
    
    Ejemplo de uso:
        # Modo simple
        panel = CTkPrecioPanel(parent, textvariable=precio_var)
        panel.pack(fill='x')
        
        # Modo multi-periodo
        precios_data = [
            {
                'periodo': periodo_obj,
                'precio': 45000.00,
                'nombre_grupo': 'Temporada Alta'
            },
            {
                'periodo': periodo_obj2,
                'precio': 'Consultar',
                'nombre_grupo': 'Temporada Media'
            }
        ]
        panel.mostrar_precios_multiples(precios_data)
    """
    
    def __init__(self, parent, textvariable=None, **kwargs):
        """Inicializa el panel de precio.
        
        Args:
            parent: Widget padre
            textvariable (tk.StringVar, optional): Variable para el precio
            **kwargs: Argumentos adicionales para CTkCard
        """
        self.precio_var = textvariable
        
        super().__init__(parent, title="PRECIO POR NOCHE", icon=Icons.DOLLAR, **kwargs)
        
        # Suscribirse a cambios del precio
        if self.precio_var:
            self.precio_var.trace_add('write', self._on_precio_changed)
    
    def _setup_ui(self):
        """Construye la estructura del panel."""
        super()._setup_ui()
        
        # Mensaje inicial
        self._mostrar_mensaje("(ninguna seleccionada)")
    
    def _mostrar_mensaje(self, mensaje):
        """Muestra un mensaje cuando no hay precio.
        
        Args:
            mensaje (str): Mensaje a mostrar
        """
        # Limpiar contenido anterior
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        label = ctk.CTkLabel(
            self.content_frame,
            text=mensaje,
            font=(Typography.FAMILY, Typography.BODY),
            text_color=Colors.TEXT_DISABLED
        )
        label.pack(expand=True, pady=40)
    
    def mostrar_precios_multiples(self, precios_data, gap_analysis=None):
        """Muestra múltiples precios organizados por periodo.

        Args:
            precios_data (list): Lista de dicts con estructura:
                {
                    'periodo': Periodo,  # Objeto con fecha_inicio, fecha_fin
                    'precio': float | str,  # Precio numérico o texto
                    'nombre_grupo': str  # Nombre del grupo de periodo
                }
            gap_analysis: GapAnalysis opcional — si tiene gaps, muestra advertencia visual
        """
        # Limpiar contenido
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if not precios_data:
            self._mostrar_mensaje("(Ingrese fechas para ver precios)")
            return

        # Siempre usar CTkScrollableFrame — CTk muestra/oculta la scrollbar
        # automáticamente según si el contenido excede el área visible.
        # NUNCA condicionar esto con un número hardcodeado (ej: "si hay > 3 items"):
        # la cantidad de items que "caben" depende del tamaño de la ventana y la
        # resolución del usuario, por lo que cualquier threshold fijo va a clipear
        # contenido silenciosamente en pantallas pequeñas o con muchos periodos.
        scroll_frame = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color="transparent",
            scrollbar_button_color=Colors.PRIMARY,
            scrollbar_button_hover_color=Colors.PRIMARY_HOVER
        )
        scroll_frame.pack(fill='both', expand=True)

        _sb = scroll_frame._scrollbar
        _canvas = scroll_frame._parent_canvas

        def _auto_hide(lo, hi):
            _sb.set(lo, hi)
            should_show = not (float(lo) <= 0.005 and float(hi) >= 0.995)
            _canvas.after(0, _sb.grid if should_show else _sb.grid_remove)

        _canvas.configure(yscrollcommand=_auto_hide)

        def _fix_scrollbar_wheel(event):
            _canvas.yview_scroll(int(-event.delta / 6), "units")
            return "break"

        _sb._canvas.bind("<MouseWheel>", _fix_scrollbar_wheel)

        container = scroll_frame

        # Crear entrada por cada periodo
        for item in precios_data:
            self._crear_precio_item(container, item)

        # Advertencia visual si hay gaps — al final, debajo de los periodos
        if gap_analysis and gap_analysis.tiene_gaps:
            self._mostrar_advertencia_gaps_en(container, gap_analysis)

    def _mostrar_advertencia_gaps_en(self, parent, gap_analysis):
        """Muestra un banner de advertencia de cobertura parcial al final de los periodos."""
        advertencia_frame = ctk.CTkFrame(
            parent,
            fg_color="#FFF3CD",
            corner_radius=Spacing.RADIUS_MD,
            border_width=1,
            border_color="#FFCA28",
        )
        advertencia_frame.pack(fill='x', pady=(Spacing.SM, 0))

        ctk.CTkLabel(
            advertencia_frame,
            text="  Cobertura parcial — hay fechas sin precio Excel",
            image=Icons.ALERT,
            compound="left",
            font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
            text_color="#856404",
            anchor='w',
        ).pack(fill='x', padx=Spacing.SM, pady=(Spacing.XS, 0))

        ctk.CTkLabel(
            advertencia_frame,
            text=gap_analysis.get_gap_description(),
            font=(Typography.FAMILY, Typography.SMALL),
            text_color="#856404",
            anchor='w',
            justify='left',
        ).pack(fill='x', padx=Spacing.SM, pady=(0, Spacing.XS))
    
    def _crear_precio_item(self, parent, item):
        """Crea un item de precio individual.
        
        Args:
            parent: Widget padre donde colocar el item
            item (dict): Datos del precio
        """
        periodo = item['periodo']
        precio = item['precio']
        nombre_grupo = item['nombre_grupo']
        
        # Frame por periodo con gradiente azul
        periodo_frame = ctk.CTkFrame(
            parent,
            fg_color=Colors.PRIMARY_LIGHT,
            corner_radius=Spacing.RADIUS_MD,
            border_width=1,
            border_color=Colors.BORDER
        )
        periodo_frame.pack(fill='x', pady=Spacing.SM)
        
        # Contenedor interno con padding
        inner_frame = ctk.CTkFrame(
            periodo_frame,
            fg_color="transparent"
        )
        inner_frame.pack(fill='both', expand=True, padx=Spacing.SM, pady=Spacing.SM)
        
        # Nombre del grupo
        ctk.CTkLabel(
            inner_frame,
            text=f"Periodo: {nombre_grupo}",
            font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
            text_color=Colors.TEXT_PRIMARY,
            anchor='w'
        ).pack(fill='x', pady=(0, 2))
        
        # Fechas con ícono
        fecha_inicio_str = periodo.fecha_inicio.strftime("%d/%m/%Y")
        fecha_fin_str = periodo.fecha_fin.strftime("%d/%m/%Y")
        fecha_str = f"📅 {fecha_inicio_str} - {fecha_fin_str}"
        
        fecha_frame = ctk.CTkFrame(
            inner_frame,
            fg_color=Colors.SURFACE,
            corner_radius=Spacing.RADIUS_SM
        )
        fecha_frame.pack(fill='x', pady=2)
        
        ctk.CTkLabel(
            fecha_frame,
            text=fecha_str,
            font=(Typography.FAMILY, Typography.SMALL),
            text_color=Colors.TEXT_SECONDARY,
            anchor='w'
        ).pack(fill='x', padx=Spacing.XS, pady=Spacing.XS)
        
        # Precio (estilo diferente según tipo)
        if isinstance(precio, (int, float)):
            # Precio numérico: destacado con fondo verde
            precio_texto = f"💵 ${precio:,.2f}"
            precio_fg = Colors.SUCCESS_LIGHT
            precio_color = Colors.SUCCESS
            font_weight = Typography.BOLD
        else:
            # Precio leyenda: más sutil
            precio_texto = f"💵 {precio}"
            precio_fg = Colors.SURFACE
            precio_color = Colors.TEXT_SECONDARY
            font_weight = Typography.NORMAL
        
        precio_frame = ctk.CTkFrame(
            inner_frame,
            fg_color=precio_fg,
            corner_radius=Spacing.RADIUS_SM
        )
        precio_frame.pack(fill='x', pady=(2, 0))
        
        precio_label = ctk.CTkLabel(
            precio_frame,
            text=precio_texto,
            font=(Typography.FAMILY, Typography.BODY, font_weight),
            text_color=precio_color,
            anchor='w'
        )
        precio_label.pack(fill='x', padx=Spacing.SM, pady=Spacing.SM)
    
    def _on_precio_changed(self, *args):
        """Callback cuando cambia el precio."""
        # Aquí podrías implementar lógica de actualización automática
        # si el precio_var cambia
        pass
    
    def limpiar(self):
        """Limpia el panel y muestra mensaje vacío."""
        self._mostrar_mensaje("(ninguna seleccionada)")
    
    def reset(self):
        """Resetea el panel (alias de limpiar)."""
        self.limpiar()
