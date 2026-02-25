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
        """Crea el panel izquierdo con el formulario y los resultados."""
        self._panel_izq = ctk.CTkFrame(
            self._content_frame,
            fg_color=Colors.SURFACE,
            corner_radius=0,
        )
        self._panel_izq.grid(row=0, column=0, sticky="nsew")
        # row 0 = formulario (no expande), row 1 = resultados (expande con minimo)
        self._panel_izq.grid_rowconfigure(0, weight=0)
        self._panel_izq.grid_rowconfigure(1, weight=1, minsize=160)
        self._panel_izq.grid_columnconfigure(0, weight=1)

        # Frame del formulario (sin scroll: la ventana tiene minsize que garantiza espacio).
        # Usar CTkFrame regular evita el problema de ancho del scrollbar de CTkScrollableFrame.
        form_frame = ctk.CTkFrame(self._panel_izq, fg_color="transparent")
        form_frame.grid(row=0, column=0, sticky="ew", padx=Spacing.LG, pady=(Spacing.LG, 0))

        self._crear_form_reserva(form_frame)
        self._crear_form_fechas(form_frame)
        self._crear_boton_ejecutar(form_frame)

        # VistaResultados ocupa todo el espacio restante (row=1, weight=1)
        resultados_outer = ctk.CTkFrame(
            self._panel_izq,
            fg_color="transparent",
            corner_radius=0,
        )
        resultados_outer.grid(row=1, column=0, sticky="nsew", padx=Spacing.LG, pady=(Spacing.SM, Spacing.LG))
        resultados_outer.grid_rowconfigure(1, weight=1)
        resultados_outer.grid_columnconfigure(0, weight=1)

        # Cabecera de la sección de resultados
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

        # Fecha entrada
        CTkDateInput(
            card.content_frame,
            label="Fecha de entrada",
            day_var=self.state.fecha_dia_entrada,
            month_var=self.state.fecha_mes_entrada,
            year_var=self.state.fecha_ano_entrada,
        ).pack(fill="x", pady=(0, Spacing.FORM_GAP))

        # Fecha salida
        CTkDateInput(
            card.content_frame,
            label="Fecha de salida",
            day_var=self.state.fecha_dia_salida,
            month_var=self.state.fecha_mes_salida,
            year_var=self.state.fecha_ano_salida,
        ).pack(fill="x", pady=(0, Spacing.FORM_GAP))

        # Huespedes
        huesp_frame = ctk.CTkFrame(card.content_frame, fg_color="transparent")
        huesp_frame.pack(fill="x")
        huesp_frame.grid_columnconfigure(0, weight=1)
        huesp_frame.grid_columnconfigure(1, weight=1)

        self._crear_entry_huesped(huesp_frame, "Adultos", self.state.adultos, 0)
        self._crear_entry_huesped(huesp_frame, "Ninos", self.state.ninos, 1)

    def _crear_entry_huesped(self, parent, label, variable, col):
        """Crea un entry de huesped (adultos o ninos)."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(
            row=0,
            column=col,
            sticky="ew",
            padx=(0, Spacing.SM) if col == 0 else 0,
        )

        ctk.CTkLabel(
            frame,
            text=label,
            font=(Typography.FAMILY, Typography.SMALL),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(0, Spacing.XS))

        ctk.CTkEntry(
            frame,
            textvariable=variable,
            font=(Typography.FAMILY, Typography.BODY),
            fg_color=Colors.SURFACE,
            border_color=Colors.BORDER,
            corner_radius=Spacing.RADIUS_MD,
        ).pack(fill="x")

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

        if nombres:
            self.state.hotel.set(nombres[0])
            self._on_hotel_changed(nombres[0])

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

            # Obtener indice por nombre dentro de los valores del combobox
            valores = list(self.habitacion_combo.combobox.cget("values"))
            try:
                idx = valores.index(nombre)
            except ValueError:
                return

            habitacion_unificada = self.state.habitaciones_unificadas[idx]
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
        """Limpia resultados al iniciar la comparacion."""
        self.resultado.delete("1.0", tk.END)
        self.resultado.insert(tk.END, "Iniciando comparacion...\n")

    def _on_comparison_completed(self, resultado_data):
        """Muestra el resultado de la comparacion."""
        from Core.comparador_multiperiodo import ResultadoComparacionMultiperiodo

        if isinstance(resultado_data, ResultadoComparacionMultiperiodo):
            self.vista_resultados.mostrar_resultado_multiperiodo(resultado_data)
            self.state.resultado_multiperiodo = resultado_data
            if resultado_data.tiene_discrepancias:
                self._mostrar_email_btn()
        else:
            # Resultado legacy (compatibilidad)
            self.resultado.delete("1.0", tk.END)
            mensaje = resultado_data.get("mensaje", "")
            coincide = resultado_data.get("coincide", False)
            for linea in mensaje.split("\n"):
                tag = ("bold",) if ("Habitacion web" in linea or "diferencia" in linea or "coinciden" in linea) else ()
                self.resultado.insert(tk.END, linea + "\n", tag)
            if coincide:
                self._mostrar_email_btn()

    def _on_comparison_error(self, error_msg):
        """Muestra el error de la comparacion en el area de resultados."""
        if "Validacion fallida" in error_msg:
            return
        self.resultado.insert(tk.END, "Error: ", ("bold",))
        self.resultado.insert(tk.END, f"{error_msg}\n")

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
            self.precio_panel.content_frame,
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
        """Abre una ventana Toplevel para redactar y enviar el email."""
        ventana = tk.Toplevel(self.root)
        ventana.title("Enviar Email")
        ventana.geometry("600x450")
        ventana.resizable(True, True)

        from tkinter import ttk

        ttk.Label(ventana, text="Contenido del Email:").pack(padx=10, pady=(10, 4), anchor="w")

        email_text = tk.Text(ventana, wrap="word", font=self.fonts.resultado)
        email_text.pack(fill="both", expand=True, padx=10, pady=4)

        # Generar texto predeterminado
        if getattr(self.state, "resultado_multiperiodo", None):
            texto = generar_texto_email_multiperiodo(
                self.state.hotel.get(),
                self.state.resultado_multiperiodo,
            )
        else:
            texto = ""
        email_text.insert(tk.END, texto)

        remitente = "gerlucero1997@gmail.com"
        destinatario = "gerlucero1977@gmail.com"

        def _enviar():
            contenido = email_text.get("1.0", tk.END).strip()
            if not contenido:
                messagebox.showerror("Error", "El contenido no puede estar vacio.", parent=ventana)
                return

            lbl_status = ttk.Label(ventana, text="Enviando...")
            lbl_status.pack(pady=4)
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
                    self.root.after(0, lambda: messagebox.showerror("Error", f"No se pudo enviar:\n{e}", parent=ventana))

            threading.Thread(target=_tarea, daemon=True).start()

        ttk.Button(ventana, text="Enviar Email", command=_enviar).pack(pady=10)


def run_interfaz():
    """Punto de entrada para la interfaz CustomTkinter."""
    root = ctk.CTk()
    app = CrawlCompareGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_interfaz()
