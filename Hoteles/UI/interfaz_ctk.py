"""Interfaz principal de la aplicacion - Version CustomTkinter.

Migra InterfazApp (interfaz.py) a CustomTkinter manteniendo toda la
logica de negocio, controladores y EventBus intactos.
"""

from debug_config import DEBUG_STARTUP_EXCEL_LOAD
import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog, messagebox
from Core.controller import GestorService, dar_hoteles_excel
from Core.excel_resolver import resolver_excel_inicial
from Core.services import ConfigService
from UI.state.event_bus import EventBus
from UI.state.app_state import AppState
from UI.styles.fonts import FontManager
from UI.styles import Colors, Typography, Spacing
from UI.styles.button_styles import secondary_button
from UI.styles.icons import Icons
from UI.components import (
    CTkCard,
    CTkLabeledComboBox,
    CTkCustomDropdown,
    CTkDateInput,
    CTkPrecioPanel,
    CTkPeriodosPanel,
)
from UI.views import ConfigModal, HistorialModal, ResultadosModal
from UI.services.historial_service import HistorialService
from UI.controllers import (
    ControladorHotel,
    ControladorValidacion,
    ControladorComparacion,
    ControladorPrecios,
)


class CrawlCompareGUI:
    """Interfaz principal de la aplicacion - Version CustomTkinter."""

    def __init__(self, root):
        """Inicializa la interfaz.

        Args:
            root: Ventana raiz CTk (customtkinter.CTk)
        """
        self.root = root
        self._configurar_ventana()

        # Infraestructura
        self.event_bus = EventBus()
        self.state = AppState(self.event_bus)
        self.fonts = FontManager(self.root)

        # Config + carga inicial del Excel.
        # GestorService.cargar puede fallar (Excel corrupto) — diferimos el
        # mensaje hasta que la UI esté armada para mostrarlo con messagebox.
        self.config_service = ConfigService()
        self.historial_service = HistorialService(self.config_service)
        self._modales_comparacion = {}   # comparison_id → ResultadosModal
        self._ctx_pendiente = None       # contexto del intento en curso (para gap modal)
        self._error_excel_inicial = None
        excel_path = resolver_excel_inicial(self.config_service)
        if excel_path:
            try:
                GestorService.cargar(excel_path)
                self.config_service.set_last_excel_path(excel_path)
                if DEBUG_STARTUP_EXCEL_LOAD:
                    print(f"[startup] Excel cargado: {excel_path}")
            except Exception as e:
                if DEBUG_STARTUP_EXCEL_LOAD:
                    print(f"[startup] Error cargando Excel inicial: {e}")
                self._error_excel_inicial = (excel_path, str(e))
        else:
            if DEBUG_STARTUP_EXCEL_LOAD:
                print("[startup] Sin Excel — arranque vacío.")

        # Aliases de compatibilidad con controladores legacy
        self.seleccion_hotel = self.state.hotel
        self.seleccion_edificio = self.state.edificio
        self.seleccion_habitacion_excel = self.state.habitacion

        self._inicializar_controladores()
        self._configurar_event_listeners()
        Icons.load()
        self._crear_interfaz()
        self._cargar_hoteles_excel()

        # Si no quedó un Excel cargado, ajustamos la UI a "modo vacío".
        if not GestorService.esta_cargado():
            self._aplicar_modo_sin_excel()
        else:
            self._actualizar_label_excel(GestorService.get_current_path())

        # Mostrar error diferido (si lo hubo) después de pintar la UI
        if self._error_excel_inicial:
            path, err = self._error_excel_inicial
            self.root.after(100, lambda: messagebox.showerror(
                "Error cargando Excel",
                f"No se pudo cargar el archivo configurado:\n{path}\n\n"
                f"Detalle: {err}\n\n"
                "Seleccioná un archivo Excel desde la barra superior."
            ))

        # Binding global Shift+Enter
        self.root.bind("<Shift-Return>", lambda e: self._ejecutar_comparacion())

    # =========================================================
    # Configuracion inicial
    # =========================================================

    def _configurar_ventana(self):
        """Configura la ventana principal CustomTkinter."""
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.root.title("Comparador de Precios de Hoteles")
        self.root.configure(fg_color=Colors.BACKGROUND)

        # Calcular tamanio inicial que quepa en la pantalla disponible
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w = min(1400, int(screen_w * 0.92))
        win_h = min(860, int(screen_h * 0.88))
        x = (screen_w - win_w) // 2
        y = max(0, (screen_h - win_h) // 2 - 20)
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.root.minsize(900, 600)

    def _inicializar_controladores(self):
        """Inicializa todos los controladores (sin cambios respecto al legacy)."""
        self.controlador_validacion = ControladorValidacion(self.state)
        self.controlador_hotel = ControladorHotel(self.state, self.event_bus)
        self.controlador_comparacion = ControladorComparacion(
            self.state,
            self.event_bus,
            self.controlador_validacion,
        )
        self.controlador_precios = ControladorPrecios(self.state, self.event_bus)

    def _configurar_event_listeners(self):
        """Suscribe los handlers a los eventos del EventBus."""
        self.event_bus.on("comparison_started", self._on_comparison_started)
        self.event_bus.on("precios_actualizados", self._on_precios_actualizados)
        self.event_bus.on("gaps_detected", self._on_gaps_detected)
        self.event_bus.on("mostrar_modal_gaps", self._on_mostrar_modal_gaps)
        self.event_bus.on("validation_failed", self._on_validation_failed)
        self.event_bus.on("hoteles_recargados", self._on_hoteles_recargados)

    # =========================================================
    # Construccion de la interfaz
    # =========================================================

    def _crear_interfaz(self):
        """Construye toda la interfaz grafica."""
        self._crear_header()

        # Contenedor central (izquierda + derecha)
        self._content_frame = ctk.CTkFrame(self.root, fg_color=Colors.BACKGROUND)
        self._content_frame.pack(fill="both", expand=True)

        # NOTA: sin uniform="cols" a propósito. El uniform forzaba a Tk a re-resolver
        # el sistema de restricciones proporcional de ambas columnas en CADA evento
        # <Configure> del resize, y como cada columna contiene un CTkScrollableFrame
        # (canvas + interior con reqwidth dinámico), ese recálculo se propagaba en
        # cascada → freeze al arrastrar el borde. weight mantiene la proporción 65/35
        # y minsize evita el colapso. El "salto de ancho" que motivó el uniform ya
        # está resuelto por el overlay place() de la scrollbar (Fix 1 en _crear_panel_izquierdo).
        self._content_frame.grid_columnconfigure(0, weight=65, minsize=480)
        self._content_frame.grid_columnconfigure(1, weight=35, minsize=360)
        self._content_frame.grid_rowconfigure(0, weight=1)

        self._crear_panel_izquierdo()
        self._crear_panel_derecho()

    def _crear_header(self):
        """Crea la barra de titulo con indicador del Excel y botón de Configuración."""
        header = ctk.CTkFrame(
            self.root,
            fg_color=Colors.HEADER_BG,
            corner_radius=0,
            height=56,
        )
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Izquierda: título
        ctk.CTkLabel(
            header,
            text="Comparador de Precios de Hoteles",
            font=(Typography.FAMILY, 18, Typography.BOLD),
            text_color=Colors.HEADER_TEXT,
        ).pack(side="left", padx=Spacing.LG, pady=Spacing.MD)

        self.btn_historial = ctk.CTkButton(
            header,
            text=" Historial",
            image=Icons.CLOCK,
            width=110,
            height=32,
            font=(Typography.FAMILY, Typography.SMALL),
            corner_radius=4,
            command=self._abrir_historial,
            **secondary_button(),
        )
        self.btn_historial.pack(side="left", padx=(Spacing.SM, 0), pady=Spacing.SM)

        # Derecha (orden inverso por pack side="right"):
        #   [label Excel]  [Cambiar]  [⚙]

        # Botón ⚙ Configuración
        self.btn_config = ctk.CTkButton(
            header,
            text="",
            image=Icons.SETTINGS_HEADER,
            width=36,
            height=32,
            fg_color="transparent",
            hover_color="#334155",
            command=self._abrir_modal_config,
        )
        self.btn_config.pack(side="right", padx=(Spacing.XS, Spacing.LG), pady=Spacing.SM)

        # Botón "Cambiar"
        self.btn_cambiar_excel = ctk.CTkButton(
            header,
            text="Cambiar",
            width=84,
            height=32,
            font=(Typography.FAMILY, Typography.SMALL),
            command=self._on_cambiar_excel,
            **secondary_button(),
        )
        self.btn_cambiar_excel.pack(side="right", padx=Spacing.XS, pady=Spacing.SM)

        # Label del Excel actual (se inicializa en _actualizar_label_excel)
        self.label_excel = ctk.CTkLabel(
            header,
            text=" Cargando…",
            image=Icons.FOLDER_HEADER,
            compound="left",
            font=(Typography.FAMILY, Typography.SMALL),
            text_color=Colors.HEADER_TEXT,
        )
        self.label_excel.pack(side="right", padx=(Spacing.LG, Spacing.SM), pady=Spacing.MD)

    def _crear_panel_izquierdo(self):
        """Crea el panel izquierdo con el formulario y los resultados (scrollable)."""
        # Contenedor externo que ocupa toda la celda del grid
        self._panel_izq_outer = ctk.CTkFrame(
            self._content_frame,
            fg_color=Colors.SURFACE,
            corner_radius=0,
        )
        self._panel_izq_outer.grid(row=0, column=0, sticky="nsew")
        self._panel_izq_outer.grid_rowconfigure(0, weight=1)
        self._panel_izq_outer.grid_columnconfigure(0, weight=1)

        # Panel scrollable: solo formulario + progress
        self._panel_izq = ctk.CTkScrollableFrame(
            self._panel_izq_outer,
            fg_color=Colors.SURFACE,
            corner_radius=0,
        )
        self._panel_izq.grid(row=0, column=0, sticky="nsew")
        self._panel_izq.grid_columnconfigure(0, weight=1)
        self._panel_izq.grid_rowconfigure(0, weight=0)   # form: alto fijo

        _sb_izq = self._panel_izq._scrollbar
        _parent_canvas = self._panel_izq._parent_canvas

        # Fix 1: auto-ocultar scrollbar con overlay (place), sin tocar el grid.
        # grid_remove/grid cambia el req de _parent_frame → uniform recalcula →
        # el panel salta de ancho. Sacamos la scrollbar del grid UNA sola vez y
        # la reposicionamos con place() sobre el canvas cuando hay overflow real.
        # Así _parent_frame siempre tiene una sola columna → req estable → sin shift.
        _sb_izq.grid_remove()
        _sb_izq.configure(width=Spacing.SCROLLBAR_WIDTH)   # CTk.place() no acepta width — se fija acá

        def _auto_hide_izq(lo, hi):
            _sb_izq.set(lo, hi)
            should_show = not (float(lo) <= 0.005 and float(hi) >= 0.995)

            def _aplicar():
                if should_show:
                    _sb_izq.place(relx=1.0, rely=0.0, relheight=1.0, anchor="ne")
                else:
                    _sb_izq.place_forget()

            _parent_canvas.after(0, _aplicar)

        _parent_canvas.configure(yscrollcommand=_auto_hide_izq)

        # Fix 2: velocidad uniforme al scrollear sobre la scrollbar (delta/40 lento → delta/6 normal).
        def _fix_scrollbar_wheel(event):
            _parent_canvas.yview_scroll(int(-event.delta / 6), "units")
            return "break"
        _sb_izq._canvas.bind("<MouseWheel>", _fix_scrollbar_wheel)

        # Contenido dentro del scrollable
        form_frame = ctk.CTkFrame(self._panel_izq, fg_color="transparent")
        form_frame.grid(row=0, column=0, sticky="ew", padx=Spacing.LG, pady=(Spacing.LG, 0))
        form_frame.columnconfigure(0, weight=1)

        self._crear_form_reserva(form_frame)
        self._crear_form_fechas(form_frame)
        self._crear_boton_ejecutar(form_frame)


    def _crear_form_reserva(self, parent):
        """Crea la card de seleccion de reserva."""
        card = CTkCard(parent, title="SELECCION DE RESERVA", icon=Icons.HOME)
        card.pack(fill="x", pady=(0, Spacing.MD))

        ctk.CTkButton(
            card.title_frame,
            text=" Limpiar",
            image=Icons.TRASH,
            width=80,
            height=24,
            font=(Typography.FAMILY, Typography.SMALL),
            corner_radius=Spacing.RADIUS_SM,
            command=self._limpiar_campos,
            **secondary_button(),
        ).pack(side="right")

        # Row que contiene hotel (siempre) + edificio (condicional, a su derecha)
        self._hotel_edificio_row = ctk.CTkFrame(card.content_frame, fg_color="transparent")
        self._hotel_edificio_row.pack(fill="x", pady=(0, Spacing.FORM_GAP))

        # Hotel
        self.hotel_combo = CTkLabeledComboBox(
            self._hotel_edificio_row,
            label="Hotel",
            textvariable=self.state.hotel,
            max_visible=3,
        )
        self.hotel_combo.pack(side="left", fill="x", expand=True)
        self.hotel_combo.combobox.configure(command=self._on_hotel_changed)

        # Edificio (oculto por defecto, se muestra a la derecha del hotel)
        self.edificio_combo = CTkLabeledComboBox(
            self._hotel_edificio_row,
            label="Edificio",
            textvariable=self.state.edificio,
            max_visible=3,
        )
        self.edificio_combo.combobox.configure(command=self._on_edificio_changed)
        # No se empaqueta todavia

        # Habitacion
        self.habitacion_combo = CTkLabeledComboBox(
            card.content_frame,
            label="Habitacion",
            textvariable=self.state.habitacion,
            max_visible=4,
        )
        self.habitacion_combo.pack(fill="x")
        self.habitacion_combo.combobox.configure(command=self._on_habitacion_changed)

        # on_confirm: Enter en un combo mueve el foco al siguiente campo
        # Se configura después de crear todos los combos pero antes de _crear_form_fechas.
        # fecha_entrada_input se asigna en _crear_form_fechas, así que usamos lambda
        # para capturarlo en tiempo de ejecución (no en tiempo de definición).
        self.hotel_combo.combobox.configure(
            on_confirm=lambda: (
                self.edificio_combo.combobox._activar_modo_busqueda()
                if self._edificio_visible
                else self.habitacion_combo.combobox._activar_modo_busqueda()
            )
        )
        self.edificio_combo.combobox.configure(
            on_confirm=lambda: self.habitacion_combo.combobox._activar_modo_busqueda()
        )
        self.habitacion_combo.combobox.configure(
            on_confirm=lambda: self.fecha_entrada_input.day_entry.focus_set()
        )

        self._edificio_visible = False

    def _crear_form_fechas(self, parent):
        """Crea la card de fechas y huespedes."""
        card = CTkCard(parent, title="FECHAS Y HUESPEDES", icon="📅")
        card.pack(fill="x", pady=(0, Spacing.MD))

        # Trazar cambios en fechas para armar la fecha completa
        for var in (
            self.state.fecha_dia_entrada,
            self.state.fecha_mes_entrada,
            self.state.fecha_ano_entrada,
        ):
            var.trace_add("write", self._actualizar_fecha_entrada)

        for var in (
            self.state.fecha_dia_salida,
            self.state.fecha_mes_salida,
            self.state.fecha_ano_salida,
        ):
            var.trace_add("write", self._actualizar_fecha_salida)

        # Fechas + huéspedes en la misma fila: [entrada | salida | adultos | niños]
        fechas_row = ctk.CTkFrame(card.content_frame, fg_color="transparent")
        fechas_row.pack(fill="x", pady=(0, Spacing.FORM_GAP))
        fechas_row.columnconfigure(0, weight=0)
        fechas_row.columnconfigure(1, weight=0)
        fechas_row.columnconfigure(2, weight=0)
        fechas_row.columnconfigure(3, weight=0)

        self.fecha_entrada_input = CTkDateInput(
            fechas_row,
            label="Fecha de entrada",
            day_var=self.state.fecha_dia_entrada,
            month_var=self.state.fecha_mes_entrada,
            year_var=self.state.fecha_ano_entrada,
        )
        self.fecha_entrada_input.grid(row=0, column=0, sticky="w", padx=(0, Spacing.MD))

        CTkDateInput(
            fechas_row,
            label="Fecha de salida",
            day_var=self.state.fecha_dia_salida,
            month_var=self.state.fecha_mes_salida,
            year_var=self.state.fecha_ano_salida,
        ).grid(row=0, column=1, sticky="w", padx=(0, Spacing.MD))

        self._crear_entry_huesped(fechas_row, "Adultos", self.state.adultos, 2, padx=(Spacing.MD, Spacing.SM))
        self._crear_entry_huesped(fechas_row, "Ninos", self.state.ninos, 3, padx=(0, 0))

    def _crear_entry_huesped(self, parent, label, variable, col, padx=0):
        """Crea un entry de huesped (adultos o ninos) con ancho compacto."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=col, sticky="nw", padx=padx)

        ctk.CTkLabel(
            frame,
            text=label,
            font=(Typography.FAMILY, Typography.BODY, Typography.BOLD),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w", pady=(0, Spacing.XXS))

        ctk.CTkEntry(
            frame,
            textvariable=variable,
            font=(Typography.FAMILY, Typography.BODY),
            fg_color=Colors.SURFACE,
            border_color=Colors.BORDER,
            border_width=1,
            corner_radius=Spacing.RADIUS_MD,
            height=32,
            width=60,
            justify='center',
            text_color=Colors.TEXT_PRIMARY,
        ).pack()

    def _crear_boton_ejecutar(self, parent):
        """Crea el boton principal de ejecucion."""
        self.btn_ejecutar = ctk.CTkButton(
            parent,
            text="Ejecutar Comparacion",
            font=(Typography.FAMILY, Typography.BODY, Typography.BOLD),
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
            text_color=Colors.HEADER_TEXT,
            corner_radius=Spacing.RADIUS_MD,
            height=44,
            command=self._ejecutar_comparacion,
        )
        self.btn_ejecutar.pack(fill="x", pady=(0, Spacing.MD))

    def _crear_panel_derecho(self):
        """Crea el panel derecho con precio y periodos."""
        panel_der = ctk.CTkFrame(
            self._content_frame,
            fg_color=Colors.BACKGROUND,
            corner_radius=0,
        )
        panel_der.grid(row=0, column=1, sticky="nsew")

        container = ctk.CTkFrame(panel_der, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=Spacing.LG, pady=(0, Spacing.LG))
        container.grid_rowconfigure(0, weight=1, uniform="panel")
        container.grid_rowconfigure(1, weight=1, uniform="panel")
        container.grid_columnconfigure(0, weight=1)

        # Panel de precio
        self.precio_panel = CTkPrecioPanel(
            container,
            textvariable=self.state.precio,
        )
        self.precio_panel.grid(row=0, column=0, sticky="nsew", pady=(Spacing.LG, Spacing.MD))

        # Panel de periodos
        self.periodos_panel = CTkPeriodosPanel(container)
        self.periodos_panel.grid(row=1, column=0, sticky="nsew")


    # =========================================================
    # Carga de datos
    # =========================================================

    def _cargar_hoteles_excel(self):
        """Carga los hoteles desde el Excel y puebla el combobox."""
        self.hoteles_excel = dar_hoteles_excel()
        self.state.hoteles_excel = self.hoteles_excel

        nombres = [h.nombre.replace("(A)", "").replace("(a)", "").strip() for h in self.hoteles_excel]
        self.hotel_combo.set_values(nombres)

        # No autoseleccionar — el usuario elige desde el dropdown

    def _cargar_edificios(self, hotel_nombre):
        """Carga los edificios para el hotel dado."""
        nombre = self._normalizar_nombre_hotel(hotel_nombre)
        edificios = self.controlador_hotel.cargar_edificios(nombre)
        self.edificio_combo.set_values(edificios)
        self.state.edificio.set("")
        self.habitacion_combo.set_values([])
        self.state.habitacion.set("")

    def _cargar_habitaciones(self, hotel_nombre, tipo=None):
        """Carga las habitaciones para el hotel y tipo opcionales."""
        nombre = self._normalizar_nombre_hotel(hotel_nombre)
        nombres_hab = self.controlador_hotel.cargar_habitaciones(nombre, tipo)
        self.habitacion_combo.set_values(nombres_hab)
        self.state.habitacion.set("")
        self.periodos_panel.limpiar()

    def _normalizar_nombre_hotel(self, hotel_nombre):
        """Elimina sufijos y capitaliza el nombre del hotel."""
        nombre = hotel_nombre.replace(" (a)", "").replace(" (A)", "").strip()
        return " ".join(w.capitalize() for w in nombre.split())

    # =========================================================
    # Visibilidad dinamica del edificio
    # =========================================================

    def _mostrar_edificio(self):
        """Muestra el combo de edificio a la derecha del hotel."""
        if not self._edificio_visible:
            self.edificio_combo.pack(side="left", fill="x", expand=True, padx=(Spacing.SM, 0))
            self._edificio_visible = True
            self.edificio_combo.update_idletasks()  # fuerza render del label interno

    def _ocultar_edificio(self):
        """Oculta el combo de edificio."""
        if self._edificio_visible:
            self.edificio_combo.pack_forget()
            self._edificio_visible = False

    # =========================================================
    # Event handlers - Formulario
    # =========================================================

    def _on_hotel_changed(self, value=None):
        """Se dispara cuando el usuario selecciona un hotel."""
        hotel = self.state.hotel.get()
        if not hotel:
            return

        hotel_lower = hotel.lower() + " (a)"
        self.periodos_panel.limpiar()

        hotel_encontrado = False
        for hotel_excel in self.hoteles_excel:
            if hotel_excel.nombre.lower() == hotel_lower:
                hotel_encontrado = True
                if hotel_excel.tipos:
                    self._mostrar_edificio()
                    self._cargar_edificios(hotel)
                else:
                    self._ocultar_edificio()
                    self._cargar_habitaciones(hotel)
                break

        if not hotel_encontrado:
            print(f"[WARN] Hotel no encontrado: {hotel}")

    def _on_edificio_changed(self, value=None):
        """Se dispara cuando el usuario selecciona un edificio."""
        edificio = self.state.edificio.get()
        hotel = self.state.hotel.get()
        self.periodos_panel.limpiar()
        self._cargar_habitaciones(hotel, edificio)

    def _on_habitacion_changed(self, value=None):
        """Se dispara cuando el usuario selecciona una habitacion.

        CTkComboBox pasa el valor seleccionado como argumento al command.
        """
        try:
            nombre = value or self.state.habitacion.get()
            if not nombre or not self.state.habitaciones_unificadas:
                return

            # Buscar por nombre directamente (más robusto que por índice)
            habitacion_unificada = next(
                (h for h in self.state.habitaciones_unificadas if h.nombre == nombre),
                None,
            )
            if habitacion_unificada is None:
                return

            self.event_bus.emit("habitacion_unificada_changed", habitacion_unificada)
            self._actualizar_periodos(habitacion_unificada)

        except Exception as e:
            self.periodos_panel.limpiar()
            print(f"[ERROR] _on_habitacion_changed: {type(e).__name__}: {e}")

    def _actualizar_fecha_entrada(self, *_args):
        """Consolida los campos DD/MM/AAAA de entrada en una sola variable."""
        dia = self.state.fecha_dia_entrada.get().zfill(2)
        mes = self.state.fecha_mes_entrada.get().zfill(2)
        ano = self.state.fecha_ano_entrada.get()
        if dia and mes and ano:
            self.state.fecha_entrada_completa.set(f"{dia}-{mes}-{ano}")
        else:
            self.state.fecha_entrada_completa.set("")

    def _actualizar_fecha_salida(self, *_args):
        """Consolida los campos DD/MM/AAAA de salida en una sola variable."""
        dia = self.state.fecha_dia_salida.get().zfill(2)
        mes = self.state.fecha_mes_salida.get().zfill(2)
        ano = self.state.fecha_ano_salida.get()
        if dia and mes and ano:
            self.state.fecha_salida_completa.set(f"{dia}-{mes}-{ano}")
        else:
            self.state.fecha_salida_completa.set("")

    def _actualizar_periodos(self, habitacion):
        """Actualiza el panel de periodos con los datos de la habitacion."""
        hotel_nombre = self.state.hotel.get().lower() + " (a)"
        hotel_actual = next(
            (h for h in self.hoteles_excel if h.nombre.lower() == hotel_nombre),
            None,
        )
        if not hotel_actual:
            self.periodos_panel.limpiar()
            return
        self.periodos_panel.actualizar_periodos(habitacion, hotel_actual)

    # =========================================================
    # Ejecucion de la comparacion
    # =========================================================

    def _ejecutar_comparacion(self):
        """Genera un comparison_id, guarda el contexto y lanza la comparación."""
        import datetime
        comparison_id = datetime.datetime.now().isoformat(timespec='microseconds')
        snapshot = {
            'hotel': self.state.hotel.get(),
            'edificio': self.state.edificio.get() or None,
            'habitacion': self.state.habitacion.get(),
            'fecha_entrada': self.state.fecha_entrada_completa.get(),
            'fecha_salida': self.state.fecha_salida_completa.get(),
            'adultos': self.state.adultos.get(),
            'ninos': self.state.ninos.get(),
            'periodos_precio': list(self.state.periodos_precio),
        }
        # Guardar contexto: el modal se crea en _on_comparison_started (caso normal)
        # o en _on_mostrar_modal_gaps si el usuario confirma continuar con gaps.
        self._ctx_pendiente = {'id': comparison_id, 'snapshot': snapshot}
        self.controlador_comparacion.ejecutar_comparacion_async(comparison_id)

    def _lanzar_modal_comparacion(self, comparison_id: str, snapshot: dict):
        """Crea el ResultadosModal y registra la referencia para cleanup."""
        offset = len(self._modales_comparacion)
        modal = ResultadosModal(
            parent=self.root,
            comparison_id=comparison_id,
            snapshot=snapshot,
            event_bus=self.event_bus,
            fonts=self.fonts,
            historial_service=self.historial_service,
            offset=offset,
        )
        self._modales_comparacion[comparison_id] = modal

        def _cleanup(event):
            if event.widget is modal:
                self._modales_comparacion.pop(comparison_id, None)
        modal.bind('<Destroy>', _cleanup)

    # =========================================================
    # Event handlers - EventBus
    # =========================================================

    def _on_comparison_started(self, data):
        """Crea el ResultadosModal para esta comparación."""
        ctx = self._ctx_pendiente
        if not ctx:
            return
        comparison_id = data.get('comparison_id') if isinstance(data, dict) else None
        if comparison_id != ctx.get('id'):
            return
        def _act():
            self._lanzar_modal_comparacion(ctx['id'], ctx['snapshot'])
            self._ctx_pendiente = None
        self.root.after(0, _act)

    def _on_precios_actualizados(self, data):
        """Actualiza el panel de precios segun el evento recibido."""
        tipo = data.get("tipo")
        gap_analysis = data.get("gap_analysis")
        if tipo in ("sin_fechas", "sin_periodos"):
            self.precio_panel._mostrar_mensaje(data["mensaje"])
        elif tipo == "precios_calculados":
            self.precio_panel.mostrar_precios_multiples(data["precios"], gap_analysis)

    def _on_gaps_detected(self, data):
        """Handler cuando se detectan gaps. El panel de precios ya muestra la advertencia visual."""
        pass

    def _on_mostrar_modal_gaps(self, data):
        """Muestra modal de confirmación cuando el usuario intenta comparar con gaps."""
        from UI.components.ctk_modal_advertencia_gaps import CtkModalAdvertenciaGaps

        gap_analysis = data['gap_analysis']
        ctx = self._ctx_pendiente  # snapshot del intento que disparó el gap

        def on_gap_response(confirmo):
            if confirmo and ctx:
                self.state.gap_confirmado = True
                self._lanzar_modal_comparacion(ctx['id'], ctx['snapshot'])
                self.controlador_comparacion.ejecutar_comparacion_async(ctx['id'])
            else:
                self.state.gap_confirmado = False
                self._ctx_pendiente = None

        self.root.after(0, lambda: CtkModalAdvertenciaGaps(self.root, gap_analysis, on_gap_response))

    # =========================================================
    # Funcionalidad de email
    # =========================================================

    # =========================================================
    # Selección de Excel y configuración
    # =========================================================

    def _on_cambiar_excel(self):
        """Handler del botón 'Cambiar' en la topbar.

        Abre un file picker, intenta cargar el Excel con GestorService.
        Si falla, mantiene el Excel anterior y notifica al usuario.
        Si funciona, persiste el path, refresca la UI y emite excel.loaded.
        """
        current = GestorService.get_current_path()
        initialdir = str(Path(current).parent) if current else str(Path.home())

        path = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[
                ("Archivos Excel", "*.xlsx"),
                ("Todos los archivos", "*.*"),
            ],
            initialdir=initialdir,
        )
        if not path:
            return

        try:
            GestorService.cargar(path)
        except Exception as e:
            messagebox.showerror(
                "Error al cargar Excel",
                f"No se pudo cargar el archivo:\n{path}\n\nDetalle: {e}"
            )
            return

        # Carga OK
        self.config_service.set_last_excel_path(path)
        self._actualizar_label_excel(path)
        self.btn_ejecutar.configure(state="normal")
        # ControladorHotel escucha esto y re-puebla; la UI se entera vía
        # 'hoteles_recargados'.
        self.event_bus.emit('excel.loaded', {
            'path': path,
            'nombre': Path(path).name,
        })

    def _actualizar_label_excel(self, path):
        """Refresca el label del Excel en la topbar.

        Args:
            path: ruta absoluta al Excel cargado, o None si no hay.
        """
        if not hasattr(self, "label_excel"):
            return
        if path is None:
            self.label_excel.configure(
                text=" Sin Excel cargado",
                text_color=Colors.ERROR,
            )
        else:
            nombre = Path(path).name
            display = nombre if len(nombre) <= 30 else nombre[:27] + "..."
            self.label_excel.configure(
                text=f" {display}",
                text_color=Colors.HEADER_TEXT,
            )

    def _abrir_modal_config(self):
        """Abre el modal de configuración (o lo trae al frente si ya está abierto)."""
        existente = getattr(self, "_modal_config", None)
        if existente is not None:
            try:
                if existente.winfo_exists():
                    existente.lift()
                    existente.focus_force()
                    return
            except Exception:
                pass
        self._modal_config = ConfigModal(self.root)

    def _aplicar_modo_sin_excel(self):
        """Configura la UI para el estado 'sin Excel cargado'."""
        self._actualizar_label_excel(None)
        if hasattr(self, "btn_ejecutar"):
            self.btn_ejecutar.configure(state="disabled")

    # =========================================================
    # Handlers de eventos nuevos
    # =========================================================

    def _limpiar_campos(self):
        """Resetea todos los campos del formulario y limpia los resultados."""
        self.state.reset_all()
        self._ocultar_edificio()
        nombres = [h.nombre.replace("(A)", "").replace("(a)", "").strip() for h in self.hoteles_excel]
        self.hotel_combo.set_values(nombres)
        self.periodos_panel.limpiar()
        self.precio_panel.limpiar()

    def _on_validation_failed(self, data):
        """Muestra el messagebox con todos los errores de validación.

        El orquestador (ControladorComparacion) decidió que la presentación
        es un messagebox. Se ejecuta en el main thread vía root.after.
        """
        mensajes = data.get('mensajes', '') if isinstance(data, dict) else str(data)

        def _mostrar():
            messagebox.showerror(
                "Datos incompletos o inválidos",
                "Revisá los siguientes campos:\n\n" + mensajes,
            )

        self.root.after(0, _mostrar)

    def _on_hoteles_recargados(self, nombres):
        """Refresca el combo de hoteles tras cambiar de Excel."""
        def _aplicar():
            self.hoteles_excel = self.state.hoteles_excel
            self.hotel_combo.set_values(nombres or [])
            self.state.hotel.set("")
            self.state.edificio.set("")
            self.state.habitacion.set("")
            self.periodos_panel.limpiar() if hasattr(self, "periodos_panel") else None
            # Si el panel de edificio estaba visible, lo ocultamos hasta que
            # el usuario seleccione un hotel nuevo.
            if getattr(self, "_edificio_visible", False):
                self._ocultar_edificio()

        self.root.after(0, _aplicar)

    # =========================================================
    # Historial
    # =========================================================

    def _abrir_historial(self):
        entradas = self.historial_service.obtener_todos()
        HistorialModal(
            self.root,
            entradas,
            on_restaurar=self._on_historial_restaurar,
            on_limpiar=self.historial_service.limpiar_todo,
        )

    def _on_historial_restaurar(self, entrada: dict):
        """Pre-rellena el formulario con los datos de una entrada del historial."""
        hotel = entrada.get("hotel", "")
        edificio = entrada.get("edificio") or ""
        habitacion = entrada.get("habitacion", "")
        fecha_entrada = entrada.get("fecha_entrada", "")
        fecha_salida = entrada.get("fecha_salida", "")
        adultos = entrada.get("adultos", 1)
        ninos = entrada.get("ninos", 0)

        # Hotel primero — dispara _on_hotel_changed que carga edificios/habitaciones
        self.state.hotel.set(hotel)
        self._on_hotel_changed()

        # Fechas: formato DD-MM-AAAA → separar componentes
        def _set_fecha(fecha_completa, var_dia, var_mes, var_ano):
            partes = fecha_completa.split("-") if fecha_completa else []
            if len(partes) == 3:
                var_dia.set(partes[0])
                var_mes.set(partes[1])
                var_ano.set(partes[2])

        _set_fecha(
            fecha_entrada,
            self.state.fecha_dia_entrada,
            self.state.fecha_mes_entrada,
            self.state.fecha_ano_entrada,
        )
        _set_fecha(
            fecha_salida,
            self.state.fecha_dia_salida,
            self.state.fecha_mes_salida,
            self.state.fecha_ano_salida,
        )

        self.state.adultos.set(adultos)
        self.state.ninos.set(ninos)

        # Edificio y habitación se difieren: _on_hotel_changed lanza
        # cargar_edificios/cargar_habitaciones que son síncronos, pero el
        # combo necesita un tick de render antes de aceptar set().
        def _set_edificio_habitacion():
            if edificio:
                self.state.edificio.set(edificio)
                self._on_edificio_changed()
                self.root.after(200, lambda: self.state.habitacion.set(habitacion))
            else:
                self.state.habitacion.set(habitacion)

        self.root.after(100, _set_edificio_habitacion)


def run_interfaz():
    """Punto de entrada para la interfaz CustomTkinter."""
    root = ctk.CTk()
    app = CrawlCompareGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_interfaz()
