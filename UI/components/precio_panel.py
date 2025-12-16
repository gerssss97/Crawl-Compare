"""Panel for displaying room price."""

import tkinter as tk
from tkinter import ttk
from .base_component import BaseComponent
from UI.utils import crear_scrollbar_autohide


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
        """Construye la interfaz del componente con soporte para múltiples precios."""
        # Título
        font_titulo = self.fonts.negrita if self.fonts else None
        ttk.Label(self, text="Precio de la habitación", font=font_titulo).grid(
            row=0, column=0, sticky='w', pady=(0, 5), padx=(0, 10))

        # Contenedor principal con scroll
        container_outer = tk.Frame(self, relief=tk.SOLID, borderwidth=1, bg='#F5F5F5')
        container_outer.grid(row=1, column=0, sticky='nsew', pady=(0, 15), padx=(0, 10))

        # Canvas para scrolling (altura aumentada para más espacio)
        self._canvas = tk.Canvas(container_outer, bg='#F5F5F5', highlightthickness=0, height=320)
        self._scrollbar = ttk.Scrollbar(container_outer, orient="vertical", command=self._canvas.yview)

        # Frame interno que contendrá los precios
        self._contenedor_precios = tk.Frame(self._canvas, bg='#F5F5F5')

        # Configurar scrolling con autohide
        autohide_callback = crear_scrollbar_autohide(self._canvas, self._scrollbar, layout_manager='pack')
        self._canvas.configure(yscrollcommand=autohide_callback)
        self._canvas_window = self._canvas.create_window(
            (0, 0),
            window=self._contenedor_precios,
            anchor='nw'
        )

        # Layout
        self._canvas.pack(side='left', fill='both', expand=True)
        self._scrollbar.pack(side='right', fill='y')

        # Bind para actualizar scroll region
        self._contenedor_precios.bind(
            '<Configure>',
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox('all'))
        )

        # Habilitar scroll con rueda del mouse
        self._setup_mousewheel()

        # Configurar expansión
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # Mensaje inicial
        self._mostrar_mensaje("(ninguna seleccionada)")

    def get_value(self):
        """Obtiene el precio actual.

        Returns:
            str: Precio actual como string
        """
        return self.textvariable.get()

    def set_value(self, precio):
        """Establece el precio (modo legacy - para compatibilidad).

        Args:
            precio (str): Nuevo precio a mostrar
        """
        self._mostrar_mensaje(precio)

    def reset(self):
        """Resetea el precio al valor por defecto."""
        self._mostrar_mensaje("(ninguna seleccionada)")

    def _mostrar_mensaje(self, mensaje: str):
        """Muestra un mensaje simple (cuando no hay precios).

        Args:
            mensaje (str): Mensaje a mostrar
        """
        # Limpiar
        for widget in self._contenedor_precios.winfo_children():
            widget.destroy()

        # Mostrar mensaje
        font_precio = self.fonts.precio if self.fonts else None
        tk.Label(
            self._contenedor_precios,
            text=mensaje,
            font=font_precio,
            bg='#F5F5F5',
            fg='#2C3E50',
            padx=12,
            pady=8,
            anchor='w'
        ).pack(fill='both')

    def mostrar_precios_multiples(self, precios_data):
        """Muestra múltiples precios organizados por periodo.

        Args:
            precios_data: Lista de dicts con estructura:
                {
                    'periodo': Periodo,
                    'precio': float | str,
                    'nombre_grupo': str
                }
        """
        # Limpiar contenido anterior
        for widget in self._contenedor_precios.winfo_children():
            widget.destroy()

        if not precios_data:
            self._mostrar_mensaje("(Ingrese fechas para ver precios)")
            return

        # Crear entrada por cada periodo
        for i, item in enumerate(precios_data):
            periodo = item['periodo']
            precio = item['precio']
            nombre_grupo = item['nombre_grupo']

            # Frame por periodo
            periodo_frame = tk.Frame(
                self._contenedor_precios,
                bg='#FAFAFA',
                relief=tk.SOLID,
                borderwidth=1
            )
            periodo_frame.pack(fill='x', padx=5, pady=5)

            # Nombre del grupo
            tk.Label(
                periodo_frame,
                text=f"Periodo: {nombre_grupo}",
                font=self.fonts.negrita if self.fonts else None,
                bg='#FAFAFA',
                anchor='w'
            ).pack(fill='x', padx=8, pady=(8, 2))

            # Rango de fechas
            fecha_inicio_str = periodo.fecha_inicio.strftime("%d/%m/%Y")
            fecha_fin_str = periodo.fecha_fin.strftime("%d/%m/%Y")
            fecha_str = f"({fecha_inicio_str} - {fecha_fin_str})"

            tk.Label(
                periodo_frame,
                text=fecha_str,
                font=self.fonts.normal if self.fonts else None,
                bg='#FAFAFA',
                fg='#555555',
                anchor='w'
            ).pack(fill='x', padx=8, pady=2)

            # Precio
            if isinstance(precio, (int, float)):
                precio_texto = f"Precio: ${precio:.2f}"
            else:
                precio_texto = f"Precio: {precio}"

            tk.Label(
                periodo_frame,
                text=precio_texto,
                font=self.fonts.precio if self.fonts else None,
                bg='#FAFAFA',
                fg='#2C3E50',
                anchor='w'
            ).pack(fill='x', padx=8, pady=(2, 8))

            # Vincular mousewheel al frame y sus hijos DESPUÉS de crear todos los widgets
            self._bind_mousewheel_to_widget(periodo_frame)

    def _setup_mousewheel(self):
        """Configura el scroll con rueda del mouse en el canvas."""
        def _on_mousewheel(event):
            # Scroll con la rueda del mouse (Windows/Mac)
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_mousewheel_linux(event):
            # Scroll para Linux (botón 4 = arriba, botón 5 = abajo)
            if event.num == 4:
                self._canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self._canvas.yview_scroll(1, "units")

        # Guardar callbacks para uso posterior
        self._mousewheel_callback = _on_mousewheel
        self._mousewheel_linux_callback = _on_mousewheel_linux

        # Bind inicial al canvas y contenedor
        self._canvas.bind('<MouseWheel>', _on_mousewheel)
        self._canvas.bind('<Button-4>', _on_mousewheel_linux)
        self._canvas.bind('<Button-5>', _on_mousewheel_linux)

        self._contenedor_precios.bind('<MouseWheel>', _on_mousewheel)
        self._contenedor_precios.bind('<Button-4>', _on_mousewheel_linux)
        self._contenedor_precios.bind('<Button-5>', _on_mousewheel_linux)

    def _bind_mousewheel_to_widget(self, widget):
        """Vincula eventos de mousewheel a un widget específico y sus hijos recursivamente.

        Args:
            widget: Widget al que vincular los eventos
        """
        # Vincular al widget actual
        widget.bind('<MouseWheel>', self._mousewheel_callback)
        widget.bind('<Button-4>', self._mousewheel_linux_callback)
        widget.bind('<Button-5>', self._mousewheel_linux_callback)

        # Vincular recursivamente a todos los hijos
        for child in widget.winfo_children():
            self._bind_mousewheel_to_widget(child)
