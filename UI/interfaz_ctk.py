"""Interfaz principal de la aplicacion - Version CustomTkinter.

Migra InterfazApp (interfaz.py) a CustomTkinter manteniendo toda la
logica de negocio, controladores y EventBus intactos.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading

from Core.controller import (
    dar_hoteles_excel,
    generar_texto_email_multiperiodo,
    enviar_email_multiperiodo,
)
from UI.state.event_bus import EventBus
from UI.state.app_state import AppState
from UI.styles.fonts import FontManager
from UI.styles import Colors, Typography, Spacing
from UI.components import (
    CTkCard,
    CTkLabeledComboBox,
    CTkDateInput,
    CTkPrecioPanel,
    CTkPeriodosPanel,
    CTkProgressPanel,
)
from UI.views import VistaResultados
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

        # Aliases de compatibilidad con controladores legacy
        self.seleccion_hotel = self.state.hotel
        self.seleccion_edificio = self.state.edificio
        self.seleccion_habitacion_excel = self.state.habitacion

        self._inicializar_controladores()
        self._configurar_event_listeners()
        self._crear_interfaz()
        self._cargar_hoteles_excel()

        # Binding global Shift+Enter
        self.root.bind("<Shift-Return>", lambda e: self._ejecutar_comparacion())

    # =========================================================
    # Configuracion inicial
    # =========================================================

    def _configurar_ventana(self):
        """Configura la ventana principal CustomTkinter."""
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.root.title("Crawl-Compare - Comparador de Precios")
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
        self.event_bus.on("comparison_progress", self._on_comparison_progress)
        self.event_bus.on("scrape_step", self._on_scrape_step)
        self.event_bus.on("comparison_completed", self._on_comparison_completed)
        self.event_bus.on("comparison_error", self._on_comparison_error)
        self.event_bus.on("precios_actualizados", self._on_precios_actualizados)

    # =========================================================
    # Construccion de la interfaz
    # =========================================================

    def _crear_interfaz(self):
        """Construye toda la interfaz grafica."""
        self._crear_header()

        # Contenedor central (izquierda + derecha)
        self._content_frame = ctk.CTkFrame(self.root, fg_color=Colors.BACKGROUND)
        self._content_frame.pack(fill="both", expand=True)

        self._content_frame.grid_columnconfigure(0, weight=55, minsize=480)
        self._content_frame.grid_columnconfigure(1, weight=45, minsize=360)
        self._content_frame.grid_rowconfigure(0, weight=1)

        self._crear_panel_izquierdo()
        self._crear_panel_derecho()

    def _crear_header(self):
        """Crea la barra de titulo superior."""
        header = ctk.CTkFrame(
            self.root,
            fg_color=Colors.HEADER_BG,
            corner_radius=0,
            height=56,
        )
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="Crawl-Compare - Comparador de Precios",
            font=(Typography.FAMILY, 18, Typography.BOLD),
            text_color=Colors.HEADER_TEXT,
        ).pack(side="left", padx=Spacing.LG, pady=Spacing.MD)

    def _crear_panel_izquierdo(self):
        """Crea el panel izquierdo con el formulario y los resultados (scrollable)."""
        # Contenedor externo que ocupa toda la celda del grid
        panel_izq_outer = ctk.CTkFrame(
            self._content_frame,
            fg_color=Colors.SURFACE,
            corner_radius=0,
        )
        panel_izq_outer.grid(row=0, column=0, sticky="nsew")
        panel_izq_outer.grid_rowconfigure(0, weight=1)
        panel_izq_outer.grid_columnconfigure(0, weight=1)

        # Panel scrollable: formulario + resultados en una sola columna
        self._panel_izq = ctk.CTkScrollableFrame(
            panel_izq_outer,
            fg_color=Colors.SURFACE,
            corner_radius=0,
        )
        self._panel_izq.grid(row=0, column=0, sticky="nsew")
        self._panel_izq.grid_columnconfigure(0, weight=1)
        self._panel_izq.grid_rowconfigure(0, weight=0)   # form: alto fijo
        self._panel_izq.grid_rowconfigure(1, weight=0)   # progress: alto fijo
        self._panel_izq.grid_rowconfigure(2, weight=1)   # resultados: crece

        # Contenido dentro del scrollable
        form_frame = ctk.CTkFrame(self._panel_izq, fg_color="transparent")
        form_frame.grid(row=0, column=0, sticky="ew", padx=Spacing.LG, pady=(Spacing.LG, 0))
        form_frame.columnconfigure(0, weight=1)

        self._crear_form_reserva(form_frame)
        self._crear_form_fechas(form_frame)
        self._crear_boton_ejecutar(form_frame)

        # Panel de progreso (oculto hasta que comience la comparacion)
        self.progress_panel = CTkProgressPanel(
            self._panel_izq,
        )
        self.progress_panel.grid(row=1, column=0, sticky="ew", padx=Spacing.LG, pady=(Spacing.SM, 0))
        self.progress_panel.grid_remove()  # oculto hasta que comience la comparacion

        # Resultados debajo del panel de progreso, dentro del mismo scroll
        resultados_outer = ctk.CTkFrame(
            self._panel_izq,
            fg_color="transparent",
            corner_radius=0,
        )
        resultados_outer.grid(row=2, column=0, sticky="nsew", padx=Spacing.LG, pady=(Spacing.SM, Spacing.LG))
        resultados_outer.columnconfigure(0, weight=1)
        resultados_outer.rowconfigure(1, weight=1)   # VistaResultados crece

        ctk.CTkLabel(
            resultados_outer,
            text="RESULTADOS DE LA COMPARACION",
            font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", pady=(0, Spacing.XS))

        self.vista_resultados = VistaResultados(
            resultados_outer,
            fonts=self.fonts,
            bg=Colors.SURFACE,
        )
        self.vista_resultados.grid(row=1, column=0, sticky="nsew")

        # Alias de compatibilidad con codigo legacy
        self.resultado = self.vista_resultados.obtener_widget_text()

    def _crear_form_reserva(self, parent):
        """Crea la card de seleccion de reserva."""
        card = CTkCard(parent, title="SELECCION DE RESERVA", icon="🏨")
        card.pack(fill="x", pady=(0, Spacing.MD))

        # Hotel
        self.hotel_combo = CTkLabeledComboBox(
            card.content_frame,
            label="Hotel",
            textvariable=self.state.hotel,
        )
        self.hotel_combo.pack(fill="x", pady=(0, Spacing.FORM_GAP))
        self.hotel_combo.combobox.configure(command=self._on_hotel_changed)

        # Edificio (oculto por defecto, se muestra si el hotel tiene tipos)
        self.edificio_combo = CTkLabeledComboBox(
            card.content_frame,
            label="Edificio",
            textvariable=self.state.edificio,
        )
        self.edificio_combo.combobox.configure(command=self._on_edificio_changed)
        # No se empaqueta todavia

        # Habitacion
        self.habitacion_combo = CTkLabeledComboBox(
            card.content_frame,
            label="Habitacion",
            textvariable=self.state.habitacion,
        )
        self.habitacion_combo.pack(fill="x")
        self.habitacion_combo.combobox.configure(command=self._on_habitacion_changed)

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

        # Fechas entrada y salida en la misma fila
        fechas_row = ctk.CTkFrame(card.content_frame, fg_color="transparent")
        fechas_row.pack(fill="x", pady=(0, Spacing.FORM_GAP))
        fechas_row.columnconfigure(0, weight=1)
        fechas_row.columnconfigure(1, weight=1)

        CTkDateInput(
            fechas_row,
            label="Fecha de entrada",
            day_var=self.state.fecha_dia_entrada,
            month_var=self.state.fecha_mes_entrada,
            year_var=self.state.fecha_ano_entrada,
        ).grid(row=0, column=0, sticky="ew", padx=(0, Spacing.MD))

        CTkDateInput(
            fechas_row,
            label="Fecha de salida",
            day_var=self.state.fecha_dia_salida,
            month_var=self.state.fecha_mes_salida,
            year_var=self.state.fecha_ano_salida,
        ).grid(row=0, column=1, sticky="ew")

        # Huespedes (compactos, ancho fijo — no necesitan llenar toda la fila)
        huesp_frame = ctk.CTkFrame(card.content_frame, fg_color="transparent")
        huesp_frame.pack(anchor="w")

        self._crear_entry_huesped(huesp_frame, "Adultos", self.state.adultos, 0)
        self._crear_entry_huesped(huesp_frame, "Ninos", self.state.ninos, 1)

    def _crear_entry_huesped(self, parent, label, variable, col):
        """Crea un entry de huesped (adultos o ninos) con ancho compacto."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(
            row=0,
            column=col,
            sticky="w",
            padx=(0, Spacing.MD) if col == 0 else 0,
        )

        ctk.CTkLabel(
            frame,
            text=label,
            font=(Typography.FAMILY, Typography.SMALL),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w", pady=(0, Spacing.XS))

        ctk.CTkEntry(
            frame,
            textvariable=variable,
            font=(Typography.FAMILY, Typography.BODY),
            fg_color=Colors.SURFACE,
            border_color=Colors.BORDER,
            corner_radius=Spacing.RADIUS_MD,
            width=100,
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
        container.pack(fill="both", expand=True, padx=Spacing.LG, pady=Spacing.LG)

        # Panel de precio
        self.precio_panel = CTkPrecioPanel(
            container,
            textvariable=self.state.precio,
        )
        self.precio_panel.pack(fill="x", pady=(0, Spacing.MD))

        # Panel de periodos
        self.periodos_panel = CTkPeriodosPanel(container)
        self.periodos_panel.pack(fill="both", expand=True)

        # Placeholder para el boton de email (se agrega dinamicamente)
        self._btn_email = None

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
        """Muestra el combo de edificio entre hotel y habitacion."""
        if not self._edificio_visible:
            self.habitacion_combo.pack_forget()
            self.edificio_combo.pack(fill="x", pady=(0, Spacing.FORM_GAP))
            self.habitacion_combo.pack(fill="x")
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
        """Delega la ejecucion al ControladorComparacion."""
        self.controlador_comparacion.ejecutar_comparacion_async()

    # =========================================================
    # Event handlers - EventBus
    # =========================================================

    def _on_comparison_started(self, data=None):
        """Limpia resultados e inicializa el panel de progreso."""
        def _actualizar():
            self.resultado.delete("1.0", tk.END)
            self.resultado.insert(tk.END, "Iniciando comparacion...\n")
            self.btn_ejecutar.configure(state="disabled")
            self._total_periodos_progreso = 0
            # El panel se inicializa con 1 periodo temporal; se ajustara
            # al recibir el primer comparison_progress con el total real.
            self.progress_panel.iniciar(total_periodos=0)
        self.root.after(0, _actualizar)

    def _on_comparison_progress(self, data):
        """Actualiza el panel de progreso con el avance del periodo actual."""
        def _actualizar():
            periodo_actual = data.get('periodo_actual', 1)
            total = data.get('total', 1)
            estado = data.get('estado', '')

            # Inicializar indicadores la primera vez que conocemos el total
            if total != self._total_periodos_progreso:
                self._total_periodos_progreso = total
                self.progress_panel.iniciar(total_periodos=total)

            self.progress_panel.actualizar(periodo_actual, total, estado)

            # Si el estado indica que el periodo termino, marcar su indicador
            estado_lower = estado.lower()
            if "ok" in estado_lower or "coincide" in estado_lower:
                self.progress_panel.marcar_periodo(periodo_actual - 1, "ok")
            elif "discrepancia" in estado_lower:
                self.progress_panel.marcar_periodo(periodo_actual - 1, "discrepancia")
            elif "error" in estado_lower:
                self.progress_panel.marcar_periodo(periodo_actual - 1, "error")
        self.root.after(0, _actualizar)

    def _on_scrape_step(self, data):
        """Actualiza la barra de progreso con el paso actual del scraping."""
        step = data.get('step', '')
        def _actualizar():
            self.progress_panel.actualizar_step(step)
        self.root.after(0, _actualizar)

    def _on_comparison_completed(self, resultado_data):
        """Muestra el resultado de la comparacion."""
        from Core.comparador_multiperiodo import ResultadoComparacionMultiperiodo

        def _actualizar():
            self.btn_ejecutar.configure(state="normal")

            if isinstance(resultado_data, ResultadoComparacionMultiperiodo):
                # Marcar indicadores con resultado final de cada periodo
                for i, rp in enumerate(resultado_data.periodos):
                    if rp.precio_excel == "Error":
                        self.progress_panel.marcar_periodo(i, "error")
                    elif rp.coincide:
                        self.progress_panel.marcar_periodo(i, "ok")
                    else:
                        self.progress_panel.marcar_periodo(i, "discrepancia")

                exito = not resultado_data.tiene_discrepancias
                self.progress_panel.finalizar(exito=exito)
                self.root.after(1500, self.progress_panel.ocultar)

                self.vista_resultados.mostrar_resultado_multiperiodo(resultado_data)
                self.state.resultado_multiperiodo = resultado_data
                if resultado_data.tiene_discrepancias:
                    self._mostrar_email_btn()
            else:
                # Resultado legacy (compatibilidad)
                self.progress_panel.ocultar()
                self.resultado.delete("1.0", tk.END)
                mensaje = resultado_data.get("mensaje", "")
                coincide = resultado_data.get("coincide", False)
                for linea in mensaje.split("\n"):
                    tag = ("bold",) if ("Habitacion web" in linea or "diferencia" in linea or "coinciden" in linea) else ()
                    self.resultado.insert(tk.END, linea + "\n", tag)
                if coincide:
                    self._mostrar_email_btn()
        self.root.after(0, _actualizar)

    def _on_comparison_error(self, error_msg):
        """Muestra el error de la comparacion en el area de resultados."""
        def _actualizar():
            self.btn_ejecutar.configure(state="normal")
            if "Validacion fallida" in error_msg:
                return
            self.progress_panel.mostrar_error()
            self.root.after(2000, self.progress_panel.ocultar)

            # Separar URL del mensaje si viene incluida
            if "\nURL: " in error_msg:
                partes = error_msg.split("\nURL: ", 1)
                msg_limpio = partes[0].strip()
                url_str = partes[1].strip()
                self.resultado.insert(tk.END, "Error al acceder a la web:\n", ("bold",))
                self.resultado.insert(tk.END, f"{msg_limpio}\n\n")
                self.resultado.insert(tk.END, "URL intentada:\n", ("bold",))
                self.resultado.insert(tk.END, f"{url_str}\n")
            else:
                self.resultado.insert(tk.END, "Error: ", ("bold",))
                self.resultado.insert(tk.END, f"{error_msg}\n")
        self.root.after(0, _actualizar)

    def _on_precios_actualizados(self, data):
        """Actualiza el panel de precios segun el evento recibido."""
        tipo = data.get("tipo")
        if tipo in ("sin_fechas", "sin_periodos"):
            self.precio_panel._mostrar_mensaje(data["mensaje"])
        elif tipo == "precios_calculados":
            self.precio_panel.mostrar_precios_multiples(data["precios"])

    # =========================================================
    # Funcionalidad de email
    # =========================================================

    def _mostrar_email_btn(self):
        """Muestra (o actualiza) el boton de envio de email."""
        if self._btn_email is not None:
            return
        self._btn_email = ctk.CTkButton(
            self.periodos_panel.content_frame,
            text="Enviar Email",
            font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
            fg_color=Colors.SUCCESS,
            hover_color="#0D9266",
            text_color=Colors.HEADER_TEXT,
            corner_radius=Spacing.RADIUS_MD,
            height=36,
            command=self._abrir_ventana_email,
        )
        self._btn_email.pack(fill="x", pady=(Spacing.SM, 0))

    def _abrir_ventana_email(self):
        """Abre un modal CTk para redactar y enviar el email (estilo mockup)."""
        ventana = ctk.CTkToplevel(self.root)
        ventana.title("Redaccion de Email - Reporte de Discrepancias")
        ventana.geometry("860x680")
        ventana.minsize(700, 560)
        ventana.resizable(True, True)
        ventana.grab_set()  # modal

        # Generar texto predeterminado
        remitente = "gerlucero1997@gmail.com"
        destinatario = "gerlucero1977@gmail.com"
        if getattr(self.state, "resultado_multiperiodo", None):
            texto_default = generar_texto_email_multiperiodo(
                self.state.hotel.get(),
                self.state.resultado_multiperiodo,
            )
        else:
            texto_default = ""

        # ── HEADER ──────────────────────────────────────────────────────────
        header = ctk.CTkFrame(ventana, fg_color=Colors.HEADER_BG, corner_radius=0, height=52)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="Redaccion de Email - Reporte de Discrepancias",
            font=(Typography.FAMILY, 15, Typography.BOLD),
            text_color=Colors.HEADER_TEXT,
        ).pack(side="left", padx=24, pady=0)

        ctk.CTkButton(
            header,
            text="Volver",
            font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
            text_color=Colors.HEADER_TEXT,
            corner_radius=Spacing.RADIUS_SM,
            height=32,
            width=100,
            command=ventana.destroy,
        ).pack(side="right", padx=16)

        # ── SCROLL CONTAINER ────────────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(ventana, fg_color=Colors.BACKGROUND, corner_radius=0)
        scroll.pack(fill="both", expand=True)

        content = ctk.CTkFrame(scroll, fg_color="transparent")
        content.pack(fill="x", padx=28, pady=24)

        # ── DESTINATARIOS ────────────────────────────────────────────────────
        dest_frame = ctk.CTkFrame(
            content,
            fg_color=Colors.SURFACE,
            corner_radius=Spacing.RADIUS_SM,
            border_width=1,
            border_color=Colors.BORDER,
        )
        dest_frame.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            dest_frame,
            text="Destinatarios:",
            font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            dest_frame,
            text=f"Para: {destinatario}",
            font=(Typography.FAMILY, Typography.SMALL),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", padx=14, pady=(0, 8))

        # ── BANNERS: Resumen + Resultados (lado a lado, misma altura) ────────
        resultado = getattr(self.state, "resultado_multiperiodo", None)

        banners_row = ctk.CTkFrame(content, fg_color="transparent")
        banners_row.pack(fill="x", pady=(0, 16))
        banners_row.grid_columnconfigure(0, weight=1)
        banners_row.grid_columnconfigure(1, weight=1)

        # — Resumen de busqueda (columna 0) —
        banner_busqueda = ctk.CTkFrame(
            banners_row,
            fg_color=Colors.PRIMARY_LIGHT,
            corner_radius=Spacing.RADIUS_SM,
            border_width=0,
        )
        banner_busqueda.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        borde_izq = ctk.CTkFrame(banner_busqueda, fg_color=Colors.PRIMARY, corner_radius=0, width=4)
        borde_izq.pack(side="left", fill="y")

        banner_inner = ctk.CTkFrame(banner_busqueda, fg_color="transparent")
        banner_inner.pack(side="left", fill="both", expand=True, padx=14, pady=12)

        ctk.CTkLabel(
            banner_inner,
            text="Resumen de Busqueda",
            font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
            text_color="#1E40AF",
            anchor="w",
        ).pack(fill="x")

        hotel_nombre = self.state.hotel.get() if self.state.hotel.get() else "Hotel"
        hab_nombre = self.state.habitacion.get() if self.state.habitacion.get() else "Habitacion"
        lbl_hotel_hab = ctk.CTkLabel(
            banner_inner,
            text=f"{hotel_nombre}  -  {hab_nombre}",
            font=(Typography.FAMILY, Typography.SMALL),
            text_color="#1E40AF",
            anchor="w",
            justify="left",
        )
        lbl_hotel_hab.pack(fill="x")
        # wraplength = mitad del ancho del row - borde izq (4) - padx inner (14*2) - gap (6) - margen extra (10)
        banners_row.bind("<Configure>", lambda e, l=lbl_hotel_hab: l.configure(wraplength=e.width // 2 - 48), add="+")

        # — Resultados de comparacion (columna 1) —
        if resultado:
            banner_res = ctk.CTkFrame(
                banners_row,
                fg_color=Colors.WARNING_LIGHT,
                corner_radius=Spacing.RADIUS_SM,
            )
            banner_res.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

            borde_res = ctk.CTkFrame(banner_res, fg_color=Colors.WARNING, corner_radius=0, width=4)
            borde_res.pack(side="left", fill="y")

            res_inner = ctk.CTkFrame(banner_res, fg_color="transparent")
            res_inner.pack(side="left", fill="both", expand=True, padx=14, pady=12)

            ctk.CTkLabel(
                res_inner,
                text="Resultados de la Comparacion",
                font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
                text_color="#92400E",
                anchor="w",
            ).pack(fill="x", pady=(0, 6))

            for rp in resultado.periodos:
                if rp.coincide:
                    precio_fmt = f"${rp.precio_excel:,.2f}" if isinstance(rp.precio_excel, (int, float)) else str(rp.precio_excel)
                    linea = f"Precios coinciden: {precio_fmt}"
                    icono = "[OK]"
                else:
                    if isinstance(rp.diferencia, (int, float)) and isinstance(rp.precio_excel, (int, float)) and rp.precio_excel:
                        pct = (rp.diferencia / float(rp.precio_excel)) * 100
                        linea = f"Discrepancia de ${rp.diferencia:,.2f} ({pct:+.1f}%)"
                    else:
                        linea = f"Discrepancia detectada"
                    icono = "[!]"
                fecha_str = ""
                if rp.fecha_inicio_real and rp.fecha_fin_real:
                    fecha_str = f"{rp.fecha_inicio_real.strftime('%d/%m')} - {rp.fecha_fin_real.strftime('%d/%m/%Y')}: "
                elif hasattr(rp, "periodo") and rp.periodo:
                    fecha_str = f"{rp.periodo.fecha_inicio.strftime('%d/%m')} - {rp.periodo.fecha_fin.strftime('%d/%m/%Y')}: "
                lbl_rp = ctk.CTkLabel(
                    res_inner,
                    text=f"{icono}  {fecha_str}{linea}",
                    font=(Typography.FAMILY, Typography.SMALL),
                    text_color="#92400E",
                    anchor="w",
                    justify="left",
                )
                lbl_rp.pack(fill="x", pady=1)
                banners_row.bind("<Configure>", lambda e, l=lbl_rp: l.configure(wraplength=e.width // 2 - 48), add="+")

            # Habitacion web matcheada
            if resultado.habitacion_web_matcheada:
                sep = ctk.CTkFrame(res_inner, fg_color="#D97706", height=1)
                sep.pack(fill="x", pady=(8, 6))
                hab_web = resultado.habitacion_web_matcheada
                match_pct = resultado.mensaje_match or ""
                lbl_hab_web = ctk.CTkLabel(
                    res_inner,
                    text=f"[H]  Habitacion Web: {hab_web.nombre}  {match_pct}",
                    font=(Typography.FAMILY, Typography.SMALL),
                    text_color="#92400E",
                    anchor="w",
                    justify="left",
                )
                lbl_hab_web.pack(fill="x")
                banners_row.bind("<Configure>", lambda e, l=lbl_hab_web: l.configure(wraplength=e.width // 2 - 48), add="+")

        # ── EDITOR DE EMAIL ──────────────────────────────────────────────────
        ctk.CTkLabel(
            content,
            text="Contenido del Email",
            font=(Typography.FAMILY, Typography.BODY, Typography.BOLD),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        editor_frame = ctk.CTkFrame(
            content,
            fg_color=Colors.SURFACE,
            corner_radius=Spacing.RADIUS_MD,
            border_width=1,
            border_color=Colors.BORDER,
        )
        editor_frame.pack(fill="both", expand=True)

        # Toolbar
        toolbar = ctk.CTkFrame(editor_frame, fg_color="#F8FAFC", corner_radius=0, height=44)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        def _toolbar_btn(parent, texto, cmd=None):
            return ctk.CTkButton(
                parent,
                text=texto,
                font=(Typography.FAMILY, Typography.SMALL),
                fg_color=Colors.SURFACE,
                hover_color="#F1F5F9",
                text_color=Colors.TEXT_SECONDARY,
                border_width=1,
                border_color=Colors.BORDER,
                corner_radius=4,
                height=28,
                width=50,
                command=cmd,
            )

        def _copiar():
            ventana.clipboard_clear()
            ventana.clipboard_append(email_text.get("1.0", tk.END))

        _toolbar_btn(toolbar, "B").pack(side="left", padx=(10, 3), pady=8)
        _toolbar_btn(toolbar, "I").pack(side="left", padx=3, pady=8)
        _toolbar_btn(toolbar, "U").pack(side="left", padx=3, pady=8)

        sep1 = ctk.CTkFrame(toolbar, fg_color=Colors.BORDER, width=1, height=24)
        sep1.pack(side="left", padx=8, pady=10)

        _toolbar_btn(toolbar, "Copiar", _copiar).pack(side="left", padx=3, pady=8)

        sep2 = ctk.CTkFrame(toolbar, fg_color=Colors.BORDER, width=1, height=24)
        sep2.pack(side="left", padx=8, pady=10)

        _toolbar_btn(toolbar, "Deshacer").pack(side="left", padx=3, pady=8)
        _toolbar_btn(toolbar, "Rehacer").pack(side="left", padx=3, pady=8)

        # Separador toolbar / textarea
        ctk.CTkFrame(editor_frame, fg_color=Colors.BORDER, height=1).pack(fill="x")

        # Textarea
        email_text = tk.Text(
            editor_frame,
            wrap="word",
            font=(Typography.FAMILY, 13),
            fg=Colors.TEXT_PRIMARY,
            bg=Colors.SURFACE,
            relief="flat",
            bd=0,
            padx=16,
            pady=14,
            spacing1=2,
            spacing3=2,
            height=16,
        )
        email_text.pack(fill="both", expand=True, padx=0, pady=0)
        email_text.insert(tk.END, texto_default)

        # Barra de caracteres
        char_bar = ctk.CTkFrame(editor_frame, fg_color="#F8FAFC", corner_radius=0, height=28)
        char_bar.pack(fill="x")
        char_bar.pack_propagate(False)
        lbl_chars = ctk.CTkLabel(
            char_bar,
            text="0 caracteres",
            font=(Typography.FAMILY, 11),
            text_color=Colors.TEXT_SECONDARY,
            anchor="e",
        )
        lbl_chars.pack(side="right", padx=12)

        def _actualizar_chars(*_):
            n = len(email_text.get("1.0", tk.END)) - 1  # -1 por el \n final
            lbl_chars.configure(text=f"{n} caracteres")

        email_text.bind("<KeyRelease>", _actualizar_chars)
        _actualizar_chars()

        # ── HINT CTRL+ENTER ──────────────────────────────────────────────────
        hint_frame = ctk.CTkFrame(content, fg_color=Colors.BACKGROUND, corner_radius=Spacing.RADIUS_SM)
        hint_frame.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(
            hint_frame,
            text="Tip: Usa  Ctrl + Enter  para enviar rapidamente",
            font=(Typography.FAMILY, 11),
            text_color=Colors.TEXT_DISABLED,
            anchor="center",
        ).pack(pady=10)

        # ── BOTONES DE ACCION ────────────────────────────────────────────────
        # Fijos en la parte inferior (fuera del scroll)
        actions_outer = ctk.CTkFrame(ventana, fg_color=Colors.BACKGROUND, corner_radius=0, height=72)
        actions_outer.pack(fill="x", side="bottom")
        actions_outer.pack_propagate(False)

        ctk.CTkFrame(actions_outer, fg_color=Colors.BORDER, height=1).pack(fill="x")

        actions = ctk.CTkFrame(actions_outer, fg_color="transparent")
        actions.pack(fill="both", expand=True, padx=28, pady=12)
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            actions,
            text="Cancelar",
            font=(Typography.FAMILY, 14, Typography.BOLD),
            fg_color=Colors.SURFACE,
            hover_color="#F1F5F9",
            text_color=Colors.TEXT_SECONDARY,
            border_width=1,
            border_color=Colors.BORDER,
            corner_radius=Spacing.RADIUS_MD,
            height=44,
            command=ventana.destroy,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 10))

        def _enviar():
            contenido = email_text.get("1.0", tk.END).strip()
            if not contenido:
                messagebox.showerror("Error", "El contenido no puede estar vacio.", parent=ventana)
                return

            btn_enviar.configure(state="disabled", text="Enviando...")
            ventana.update()

            def _tarea():
                try:
                    enviar_email_multiperiodo(
                        hotel=self.state.hotel.get(),
                        resultado_multiperiodo=self.state.resultado_multiperiodo,
                        remitente=remitente,
                        destinatario=destinatario,
                        texto_override=contenido,
                    )
                    self.root.after(0, lambda: (ventana.destroy(), messagebox.showinfo("OK", "Email enviado correctamente.")))
                except Exception as e:
                    self.root.after(0, lambda: (
                        btn_enviar.configure(state="normal", text="Enviar Email"),
                        messagebox.showerror("Error", f"No se pudo enviar:\n{e}", parent=ventana),
                    ))

            threading.Thread(target=_tarea, daemon=True).start()

        btn_enviar = ctk.CTkButton(
            actions,
            text="Enviar Email",
            font=(Typography.FAMILY, 14, Typography.BOLD),
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
            text_color=Colors.HEADER_TEXT,
            corner_radius=Spacing.RADIUS_MD,
            height=44,
            command=_enviar,
        )
        btn_enviar.grid(row=0, column=1, sticky="ew")

        # Atajo Ctrl+Enter para enviar
        ventana.bind("<Control-Return>", lambda _: _enviar())


def run_interfaz():
    """Punto de entrada para la interfaz CustomTkinter."""
    root = ctk.CTk()
    app = CrawlCompareGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_interfaz()
