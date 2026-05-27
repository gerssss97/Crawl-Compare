"""Modal autónomo para mostrar el resultado de una comparación de precios."""

import datetime
import tkinter as tk
import customtkinter as ctk

from UI.styles import Colors, Typography, Spacing
from UI.components import CTkProgressPanel
from UI.views.vista_resultados import VistaResultados


class _FakeVar:
    """StringVar/IntVar fake para satisfacer la interfaz que ModalEmail espera de AppState."""
    def __init__(self, value):
        self._v = value

    def get(self):
        return self._v


class _FakeState:
    """AppState fake — expone solo los campos que ModalEmail necesita."""
    def __init__(self, snapshot: dict, resultado):
        self.hotel = _FakeVar(snapshot.get('hotel', ''))
        self.edificio = _FakeVar(snapshot.get('edificio') or '')
        self.habitacion = _FakeVar(snapshot.get('habitacion', ''))
        self.resultado_multiperiodo = resultado
        self.periodos_precio = []


class ResultadosModal(ctk.CTkToplevel):
    """Modal independiente que muestra el progreso y resultado de una comparación.

    Se suscribe al EventBus filtrando por comparison_id. Al cerrarse,
    se desuscribe limpiamente para evitar callbacks huérfanos.
    """

    def __init__(
        self,
        parent,
        comparison_id: str,
        snapshot: dict,
        event_bus,
        fonts,
        historial_service,
        offset: int = 0,
    ):
        super().__init__(parent)

        self._comparison_id = comparison_id
        self._snapshot = snapshot
        self._event_bus = event_bus
        self._fonts = fonts
        self._historial_service = historial_service
        self._resultado = None
        self._total_periodos_progreso = 0
        self._handlers = {}
        self._btn_email = None

        self._configurar_ventana()
        self._construir_ui()
        self._suscribir_eventos()
        self.protocol("WM_DELETE_WINDOW", self._on_cerrar)
        self.after(80, lambda: self._posicionar(parent, offset))

    # =========================================================
    # Configuración de ventana
    # =========================================================

    def _configurar_ventana(self):
        hab = self._snapshot.get('habitacion', '')
        self.title(f"Comparando: {hab[:50]}...")
        self.geometry("780x560")
        self.minsize(600, 400)
        self.resizable(True, True)
        self.configure(fg_color=Colors.SURFACE)

    # =========================================================
    # Construcción de UI
    # =========================================================

    def _construir_ui(self):
        self.grid_rowconfigure(0, weight=0)   # header con mini resumen
        self.grid_rowconfigure(1, weight=0)   # progress panel
        self.grid_rowconfigure(2, weight=1)   # vista resultados
        self.grid_rowconfigure(3, weight=0)   # botón email (aparece dinámicamente)
        self.grid_columnconfigure(0, weight=1)

        self._construir_header()
        self._construir_progress()
        self._construir_resultados()

    def _construir_header(self):
        hotel = self._snapshot.get('hotel', '')
        edificio = self._snapshot.get('edificio')
        hab = self._snapshot.get('habitacion', '')
        f_entrada = self._snapshot.get('fecha_entrada', '')
        f_salida = self._snapshot.get('fecha_salida', '')
        adultos = self._snapshot.get('adultos', 1)
        ninos = self._snapshot.get('ninos', 0)

        nombre_hotel = f"{hotel} — {edificio}" if edificio else hotel
        huesp = f"{adultos} adulto{'s' if adultos != 1 else ''}"
        if ninos:
            huesp += f", {ninos} niño{'s' if ninos != 1 else ''}"

        header = ctk.CTkFrame(
            self,
            fg_color=Colors.BACKGROUND,
            corner_radius=Spacing.RADIUS_MD,
            border_width=1,
            border_color=Colors.BORDER,
        )
        header.grid(row=0, column=0, sticky="ew", padx=Spacing.LG, pady=(Spacing.MD, Spacing.SM))
        header.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=nombre_hotel,
            font=(Typography.FAMILY, Typography.BODY, Typography.BOLD),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))

        ctk.CTkLabel(
            header,
            text=hab,
            font=(Typography.FAMILY, Typography.SMALL),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=Spacing.MD)

        ctk.CTkLabel(
            header,
            text=f"{f_entrada} → {f_salida}   •   {huesp}",
            font=(Typography.FAMILY, Typography.SMALL),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        ).grid(row=2, column=0, sticky="ew", padx=Spacing.MD, pady=(0, Spacing.SM))

        periodos = self._snapshot.get('periodos_precio') or []
        if periodos:
            self._construir_tabla_periodos(header, periodos)

    def _construir_tabla_periodos(self, parent, periodos: list):
        ctk.CTkFrame(
            parent, height=1, fg_color=Colors.BORDER,
        ).grid(row=3, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.XS, 0))

        tabla = ctk.CTkFrame(parent, fg_color="transparent")
        tabla.grid(row=4, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.SM))
        tabla.columnconfigure(0, weight=2)
        tabla.columnconfigure(1, weight=3)
        tabla.columnconfigure(2, weight=1)

        for i, entry in enumerate(periodos):
            periodo = entry['periodo']
            precio = entry['precio']
            nombre_grupo = entry.get('nombre_grupo') or ''

            etiqueta = nombre_grupo or periodo.nombre or "—"
            ctk.CTkLabel(
                tabla, text=etiqueta,
                font=(Typography.FAMILY, Typography.SMALL),
                text_color=Colors.TEXT_SECONDARY,
                anchor="w",
            ).grid(row=i, column=0, sticky="w")

            f_ini = periodo.fecha_inicio.strftime("%d/%m/%Y")
            f_fin = periodo.fecha_fin.strftime("%d/%m/%Y")
            ctk.CTkLabel(
                tabla, text=f"{f_ini} → {f_fin}",
                font=(Typography.FAMILY, Typography.SMALL),
                text_color=Colors.TEXT_SECONDARY,
                anchor="w",
            ).grid(row=i, column=1, sticky="w", padx=(Spacing.SM, 0))

            if isinstance(precio, (int, float)):
                precio_str = f"${precio:.2f}"
            else:
                precio_str = str(precio)
            ctk.CTkLabel(
                tabla, text=precio_str,
                font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
                text_color=Colors.TEXT_PRIMARY,
                anchor="e",
            ).grid(row=i, column=2, sticky="e", padx=(Spacing.SM, 0))

    def _construir_progress(self):
        self.progress_panel = CTkProgressPanel(
            self,
            grid_kwargs={
                "row": 1,
                "column": 0,
                "sticky": "ew",
                "padx": Spacing.LG,
                "pady": (0, Spacing.XS),
            },
        )
        self.progress_panel.iniciar(total_periodos=1)

    def _construir_resultados(self):
        caja = ctk.CTkFrame(
            self,
            fg_color=Colors.SURFACE,
            corner_radius=Spacing.RADIUS_MD,
            border_width=1,
            border_color=Colors.BORDER,
        )
        caja.grid(row=2, column=0, sticky="nsew", padx=Spacing.LG, pady=(0, Spacing.SM))
        caja.grid_rowconfigure(0, weight=1)
        caja.grid_columnconfigure(0, weight=1)

        self.vista_resultados = VistaResultados(caja, fonts=self._fonts, bg=Colors.SURFACE)
        self.vista_resultados.grid(row=0, column=0, sticky="nsew", padx=Spacing.SM, pady=Spacing.SM)

    # =========================================================
    # EventBus — suscripción / desuscripción
    # =========================================================

    def _suscribir_eventos(self):
        self._handlers = {
            'comparison_started':   self._on_started,
            'comparison_progress':  self._on_progress,
            'scrape_step':          self._on_scrape_step,
            'comparison_completed': self._on_completed,
            'comparison_error':     self._on_error,
        }
        for evento, handler in self._handlers.items():
            self._event_bus.on(evento, handler)

    def _desuscribir_eventos(self):
        for evento, handler in self._handlers.items():
            self._event_bus.off(evento, handler)

    def _on_cerrar(self):
        self._desuscribir_eventos()
        self.destroy()

    def _filtrar(self, data) -> bool:
        return isinstance(data, dict) and data.get('comparison_id') == self._comparison_id

    # =========================================================
    # Handlers de eventos (filtran por comparison_id)
    # =========================================================

    def _on_started(self, data):
        if not self._filtrar(data):
            return
        def _act():
            self._total_periodos_progreso = 0
            self.progress_panel.iniciar(total_periodos=0)
        self.after(0, _act)

    def _on_progress(self, data):
        if not self._filtrar(data):
            return
        def _act():
            periodo_actual = data.get('periodo_actual', 1)
            total = data.get('total', 1)
            estado = data.get('estado', '')
            if total != self._total_periodos_progreso:
                self._total_periodos_progreso = total
                self.progress_panel.iniciar(total_periodos=total)
            self.progress_panel.actualizar(periodo_actual, total, estado)
            estado_lower = estado.lower()
            if "ok" in estado_lower or "coincide" in estado_lower:
                self.progress_panel.marcar_periodo(periodo_actual - 1, "ok")
            elif "discrepancia" in estado_lower:
                self.progress_panel.marcar_periodo(periodo_actual - 1, "discrepancia")
            elif "error" in estado_lower:
                self.progress_panel.marcar_periodo(periodo_actual - 1, "error")
        self.after(0, _act)

    def _on_scrape_step(self, data):
        if not self._filtrar(data):
            return
        def _act():
            self.progress_panel.actualizar_step(data.get('step', ''))
        self.after(0, _act)

    def _on_completed(self, data):
        if not self._filtrar(data):
            return
        resultado = data.get('resultado')
        def _act():
            from Core.comparador_multiperiodo import ResultadoComparacionMultiperiodo
            if isinstance(resultado, ResultadoComparacionMultiperiodo):
                for i, rp in enumerate(resultado.periodos):
                    if rp.precio_excel == "Error":
                        self.progress_panel.marcar_periodo(i, "error")
                    elif rp.coincide:
                        self.progress_panel.marcar_periodo(i, "ok")
                    else:
                        self.progress_panel.marcar_periodo(i, "discrepancia")
                exito = not resultado.tiene_discrepancias
                self.progress_panel.finalizar(exito=exito)
                self.after(1500, self.progress_panel.ocultar)
                self.vista_resultados.mostrar_resultado_multiperiodo(resultado)
                self._resultado = resultado
                self._guardar_historial(resultado)
                estado_str = "OK" if exito else "Discrepancias"
                hab_corta = self._snapshot.get('habitacion', '')[:40]
                self.title(f"{hab_corta} — {estado_str}")
                if resultado.tiene_discrepancias:
                    self._mostrar_btn_email()
        self.after(0, _act)

    def _on_error(self, data):
        if not self._filtrar(data):
            return
        error_msg = data.get('error', 'Error desconocido')
        def _act():
            self.progress_panel.mostrar_error()
            self.after(2000, self.progress_panel.ocultar)
            widget = self.vista_resultados.obtener_widget_text()
            if "\nURL: " in error_msg:
                partes = error_msg.split("\nURL: ", 1)
                widget.insert(tk.END, "Error al acceder a la web:\n", ("bold",))
                widget.insert(tk.END, f"{partes[0].strip()}\n\n")
                widget.insert(tk.END, "URL intentada:\n", ("bold",))
                widget.insert(tk.END, f"{partes[1].strip()}\n")
            else:
                widget.insert(tk.END, "Error: ", ("bold",))
                widget.insert(tk.END, f"{error_msg}\n")
            hab_corta = self._snapshot.get('habitacion', '')[:40]
            self.title(f"{hab_corta} — Error")
        self.after(0, _act)

    # =========================================================
    # Historial y email
    # =========================================================

    def _guardar_historial(self, resultado):
        try:
            self._historial_service.agregar({
                "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
                "hotel": self._snapshot.get('hotel', ''),
                "edificio": self._snapshot.get('edificio'),
                "habitacion": self._snapshot.get('habitacion', ''),
                "fecha_entrada": self._snapshot.get('fecha_entrada', ''),
                "fecha_salida": self._snapshot.get('fecha_salida', ''),
                "adultos": self._snapshot.get('adultos', 1),
                "ninos": self._snapshot.get('ninos', 0),
                "periodos": [
                    {
                        "nombre": rp.periodo.nombre,
                        "precio_excel": rp.precio_excel,
                        "precio_web": rp.precio_web,
                        "coincide": rp.coincide,
                    }
                    for rp in resultado.periodos
                ],
            })
        except Exception as e:
            print(f"[historial] Error al guardar: {e}")

    def _mostrar_btn_email(self):
        if self._btn_email is not None:
            return
        self._btn_email = ctk.CTkButton(
            self,
            text="Enviar Email",
            font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
            fg_color=Colors.SUCCESS,
            hover_color="#0D9266",
            text_color=Colors.HEADER_TEXT,
            corner_radius=Spacing.RADIUS_MD,
            height=36,
            command=self._abrir_email,
        )
        self._btn_email.grid(
            row=3, column=0, sticky="ew",
            padx=Spacing.LG, pady=(Spacing.SM, Spacing.MD),
        )

    def _abrir_email(self):
        if not self._resultado:
            return
        from UI.views.modal_email import ModalEmail
        fake_state = _FakeState(self._snapshot, self._resultado)
        ModalEmail(self, fake_state)

    # =========================================================
    # Posicionamiento
    # =========================================================

    def _posicionar(self, parent, offset: int):
        self.update_idletasks()
        try:
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
        except Exception:
            return
        w = self.winfo_width()
        h = self.winfo_height()
        desp = offset * 28
        x = px + (pw - w) // 2 + desp
        y = py + (ph - h) // 2 + desp
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
