"""Modal de redaccion y envio de email con reporte de discrepancias."""

import threading
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from Core.controller import generar_texto_email_multiperiodo, enviar_email_multiperiodo
from UI.components import CTkCustomDropdown
from UI.styles import Colors, Typography, Spacing


class ModalEmail(ctk.CTkToplevel):
    """Modal para redactar y enviar el email de reporte de discrepancias."""

    REMITENTE = "gerlucero1997@gmail.com"
    DESTINATARIO = "gerlucero1977@gmail.com"

    def __init__(self, parent, state):
        """Inicializa el modal.

        Args:
            parent: Ventana padre (CTk root)
            state: AppState — provee hotel, habitacion y resultado_multiperiodo
        """
        super().__init__(parent)
        self._state = state

        self._configurar_ventana()

        texto_default = self._generar_texto_default()
        self._construir_ui(texto_default)

    # =========================================================
    # Configuracion
    # =========================================================

    def _configurar_ventana(self):
        self.title("Redaccion de Email - Reporte de Discrepancias")
        self.geometry("860x680")
        self.minsize(700, 560)
        self.resizable(True, True)
        self.grab_set()

    def _generar_texto_default(self):
        resultado = getattr(self._state, "resultado_multiperiodo", None)
        if resultado:
            return generar_texto_email_multiperiodo(
                self._state.hotel.get(),
                resultado,
            )
        return ""

    # =========================================================
    # Construccion de la UI
    # =========================================================

    def _construir_ui(self, texto_default):
        self._crear_header()
        scroll = ctk.CTkScrollableFrame(self, fg_color=Colors.BACKGROUND, corner_radius=0)
        scroll.pack(fill="both", expand=True)

        content = ctk.CTkFrame(scroll, fg_color="transparent")
        content.pack(fill="x", padx=28, pady=24)

        self._crear_destinatarios(content)
        self._crear_banners(content)
        self._email_text = self._crear_editor(content, texto_default)
        self._crear_hint(content)
        self._crear_botones_accion()

    def _crear_header(self):
        header = ctk.CTkFrame(self, fg_color=Colors.HEADER_BG, corner_radius=0, height=52)
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
            command=self.destroy,
        ).pack(side="right", padx=16)

    def _crear_destinatarios(self, parent):
        dest_frame = ctk.CTkFrame(
            parent,
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

        row = ctk.CTkFrame(dest_frame, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(0, 8))

        ctk.CTkLabel(
            row,
            text="Para:",
            font=(Typography.FAMILY, Typography.SMALL),
            text_color=Colors.TEXT_SECONDARY,
            width=36,
            anchor="w",
        ).pack(side="left")

        self._entry_destinatario = ctk.CTkEntry(
            row,
            font=(Typography.FAMILY, Typography.SMALL),
            fg_color=Colors.BACKGROUND,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            height=28,
            corner_radius=Spacing.RADIUS_SM,
        )
        self._entry_destinatario.insert(0, self.DESTINATARIO)
        self._entry_destinatario.pack(side="left", fill="x", expand=True, padx=(6, 0))

        self._lbl_error_dest = ctk.CTkLabel(
            dest_frame,
            text="",
            font=(Typography.FAMILY, 11),
            text_color="#DC2626",
            anchor="w",
        )
        self._lbl_error_dest.pack(fill="x", padx=14, pady=(0, 6))

        def _email_valido(valor):
            return "@" in valor and "." in valor.split("@")[-1]

        def _on_blur(_):
            valor = self._entry_destinatario.get().strip()
            if not valor:
                self._lbl_error_dest.configure(text="El destinatario no puede estar vacio.")
                self._entry_destinatario.configure(border_color="#DC2626")
            elif not _email_valido(valor):
                self._lbl_error_dest.configure(text="Formato de email invalido (ej: nombre@dominio.com)")
                self._entry_destinatario.configure(border_color="#DC2626")

        def _on_key(_):
            self._lbl_error_dest.configure(text="")
            self._entry_destinatario.configure(border_color=Colors.BORDER)

        self._entry_destinatario.bind("<FocusOut>", _on_blur)
        self._entry_destinatario.bind("<Key>", _on_key)

    def _crear_banners(self, parent):
        resultado = getattr(self._state, "resultado_multiperiodo", None)

        banners_row = ctk.CTkFrame(parent, fg_color="transparent")
        banners_row.pack(fill="x", pady=(0, 16))

        self._crear_banner_busqueda(banners_row)
        if resultado:
            self._crear_banner_resultados(banners_row, resultado)

    def _crear_banner_busqueda(self, parent):
        banner = ctk.CTkFrame(
            parent,
            fg_color=Colors.PRIMARY_LIGHT,
            corner_radius=Spacing.RADIUS_SM,
            border_width=0,
        )
        banner.pack(side="left", fill="both", expand=True, padx=(0, 6))

        ctk.CTkFrame(banner, fg_color=Colors.PRIMARY, corner_radius=0, width=4).pack(side="left", fill="y")

        inner = ctk.CTkFrame(banner, fg_color="transparent")
        inner.pack(side="left", fill="both", expand=True, padx=14, pady=12)

        ctk.CTkLabel(
            inner,
            text="Resumen de Busqueda",
            font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
            text_color="#1E40AF",
            anchor="w",
            width=1,
        ).pack(fill="x")

        hotel = self._state.hotel.get() or "Hotel"
        edificio = self._state.edificio.get() if self._state.edificio.get() else None
        hab = self._state.habitacion.get() or "Habitacion"

        if edificio:
            texto_hab = f"{hotel}  |  {edificio}  |  {hab}"
        else:
            texto_hab = f"{hotel}  |  {hab}"

        lbl = ctk.CTkLabel(
            inner,
            text=texto_hab,
            font=(Typography.FAMILY, Typography.SMALL),
            text_color="#1E40AF",
            anchor="w",
            justify="left",
            wraplength=1,
            width=1,
        )
        lbl.pack(fill="x")
        inner.bind("<Configure>", lambda e, l=lbl: l.configure(wraplength=max(1, e.width)), add="+")

        # Periodos con sus precios
        periodos_precio = getattr(self._state, "periodos_precio", [])
        if periodos_precio:
            ctk.CTkFrame(inner, fg_color="#BFDBFE", height=1).pack(fill="x", pady=(8, 6))
            for pp in periodos_precio:
                periodo = pp.get("periodo")
                precio = pp.get("precio")
                nombre_grupo = pp.get("nombre_grupo")

                nombre_periodo = nombre_grupo or (periodo.nombre if periodo else "Periodo desconocido")

                if isinstance(precio, (int, float)):
                    precio_str = f"${precio:,.2f}"
                else:
                    precio_str = str(precio) if precio else "Sin precio"

                if periodo:
                    rango_str = f"{periodo.fecha_inicio.strftime('%d/%m')} - {periodo.fecha_fin.strftime('%d/%m/%Y')}"
                    linea = f"{nombre_periodo}  ({rango_str})  →  {precio_str}"
                else:
                    linea = f"{nombre_periodo}  →  {precio_str}"

                lbl_p = ctk.CTkLabel(
                    inner,
                    text=linea,
                    font=(Typography.FAMILY, Typography.SMALL),
                    text_color="#1E40AF",
                    anchor="w",
                    justify="left",
                    wraplength=1,
                    width=1,
                )
                lbl_p.pack(fill="x", pady=1)
                inner.bind("<Configure>", lambda e, l=lbl_p: l.configure(wraplength=max(1, e.width)), add="+")

    def _crear_banner_resultados(self, parent, resultado):
        banner = ctk.CTkFrame(
            parent,
            fg_color=Colors.WARNING_LIGHT,
            corner_radius=Spacing.RADIUS_SM,
            border_width=0,
        )
        banner.pack(side="left", fill="both", expand=True, padx=(6, 0))

        ctk.CTkFrame(banner, fg_color=Colors.WARNING, corner_radius=0, width=4).pack(side="left", fill="y")

        inner = ctk.CTkFrame(banner, fg_color="transparent")
        inner.pack(side="left", fill="both", expand=True, padx=14, pady=12)

        ctk.CTkLabel(
            inner,
            text="Resultados de la Comparacion",
            font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
            text_color="#92400E",
            anchor="w",
            width=1,
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
                    linea = "Discrepancia detectada"
                icono = "[!]"

            fecha_str = ""
            if rp.fecha_inicio_real and rp.fecha_fin_real:
                fecha_str = f"{rp.fecha_inicio_real.strftime('%d/%m')} - {rp.fecha_fin_real.strftime('%d/%m/%Y')}: "
            elif hasattr(rp, "periodo") and rp.periodo:
                fecha_str = f"{rp.periodo.fecha_inicio.strftime('%d/%m')} - {rp.periodo.fecha_fin.strftime('%d/%m/%Y')}: "

            lbl = ctk.CTkLabel(
                inner,
                text=f"{icono}  {fecha_str}{linea}",
                font=(Typography.FAMILY, Typography.SMALL),
                text_color="#92400E",
                anchor="w",
                justify="left",
                wraplength=1,
                width=1,
            )
            lbl.pack(fill="x", pady=1)
            inner.bind("<Configure>", lambda e, l=lbl: l.configure(wraplength=max(1, e.width)), add="+")

        if resultado.habitacion_web_matcheada:
            ctk.CTkFrame(inner, fg_color="#D97706", height=1).pack(fill="x", pady=(8, 6))
            hab_web = resultado.habitacion_web_matcheada
            match_pct = resultado.mensaje_match or ""
            lbl_hw = ctk.CTkLabel(
                inner,
                text=f"[H]  Habitacion Web: {hab_web.nombre}  {match_pct}",
                font=(Typography.FAMILY, Typography.SMALL),
                text_color="#92400E",
                anchor="w",
                justify="left",
                wraplength=1,
                width=1,
            )
            lbl_hw.pack(fill="x")
            inner.bind("<Configure>", lambda e, l=lbl_hw: l.configure(wraplength=max(1, e.width)), add="+")

    def _crear_editor(self, parent, texto_default):
        """Crea el editor de email con toolbar. Retorna el widget tk.Text."""
        ctk.CTkLabel(
            parent,
            text="Contenido del Email",
            font=(Typography.FAMILY, Typography.BODY, Typography.BOLD),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        editor_frame = ctk.CTkFrame(
            parent,
            fg_color=Colors.SURFACE,
            corner_radius=Spacing.RADIUS_MD,
            border_width=1,
            border_color=Colors.BORDER,
        )
        editor_frame.pack(fill="both", expand=True)

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
            undo=True,
        )

        self._crear_toolbar(editor_frame, email_text)
        ctk.CTkFrame(editor_frame, fg_color=Colors.BORDER, height=1).pack(fill="x")

        email_text.pack(fill="both", expand=True)
        email_text.insert(tk.END, texto_default)

        email_text.tag_configure("bold", font=(Typography.FAMILY, 13, "bold"))
        email_text.tag_configure("italic", font=(Typography.FAMILY, 13, "italic"))
        email_text.tag_configure("underline", underline=True)

        self._crear_barra_chars(editor_frame, email_text)

        return email_text

    def _crear_toolbar(self, parent, email_text):
        FUENTES = ["Inter", "Arial", "Helvetica", "Georgia", "Courier New", "Verdana", "Times New Roman"]
        TAMANIOS = [9, 10, 11, 12, 13, 14, 16, 18, 20, 24]
        _fuente = [Typography.FAMILY]
        _tamanio = [13]

        def _btn(texto, cmd=None):
            return ctk.CTkButton(
                toolbar,
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

        def _toggle(tag):
            try:
                start = email_text.index(tk.SEL_FIRST)
                end = email_text.index(tk.SEL_LAST)
            except tk.TclError:
                return
            ranges = email_text.tag_ranges(tag)
            tiene = any(
                email_text.compare(ranges[i], "<=", start) and email_text.compare(ranges[i + 1], ">=", end)
                for i in range(0, len(ranges), 2)
            )
            if tiene:
                email_text.tag_remove(tag, start, end)
            else:
                email_text.tag_add(tag, start, end)

        def _aplicar_formato(tipo, valor):
            """Aplica fuente o tamaño solo al texto seleccionado via tag dinámico."""
            try:
                start = email_text.index(tk.SEL_FIRST)
                end = email_text.index(tk.SEL_LAST)
            except tk.TclError:
                return  # sin selección, no hace nada

            tag_name = f"fmt_{tipo}_{valor}".replace(" ", "_")
            if tipo == "fuente":
                email_text.tag_configure(tag_name, font=(valor, _tamanio[0]))
            else:  # tamanio
                email_text.tag_configure(tag_name, font=(_fuente[0], int(valor)))
            email_text.tag_add(tag_name, start, end)

        def _cambiar_fuente(f):
            _fuente[0] = f
            _aplicar_formato("fuente", f)

        def _cambiar_tamanio(t):
            _tamanio[0] = int(t)
            _aplicar_formato("tamanio", t)

        toolbar = ctk.CTkFrame(parent, fg_color="#F8FAFC", corner_radius=0, height=44)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        _btn("B", lambda: _toggle("bold")).pack(side="left", padx=(10, 3), pady=8)
        _btn("I", lambda: _toggle("italic")).pack(side="left", padx=3, pady=8)
        _btn("U", lambda: _toggle("underline")).pack(side="left", padx=3, pady=8)

        ctk.CTkFrame(toolbar, fg_color=Colors.BORDER, width=2, height=28).pack(side="left", padx=8, pady=10)

        dd_fuente = CTkCustomDropdown(toolbar, values=FUENTES, command=_cambiar_fuente, placeholder_text=Typography.FAMILY, width=160)
        dd_fuente.set(Typography.FAMILY)
        dd_fuente.pack(side="left", padx=3, pady=8)

        dd_tamanio = CTkCustomDropdown(toolbar, values=[str(t) for t in TAMANIOS], command=_cambiar_tamanio, placeholder_text="13", width=90)
        dd_tamanio.set("13")
        dd_tamanio.pack(side="left", padx=(6, 3), pady=8)

        ctk.CTkFrame(toolbar, fg_color=Colors.BORDER, width=2, height=28).pack(side="left", padx=8, pady=10)

        _btn("Deshacer", lambda: email_text.edit_undo() if True else None).pack(side="left", padx=3, pady=8)
        _btn("Rehacer", lambda: email_text.edit_redo() if True else None).pack(side="left", padx=3, pady=8)

    def _crear_barra_chars(self, parent, email_text):
        char_bar = ctk.CTkFrame(parent, fg_color="#F8FAFC", corner_radius=0, height=28)
        char_bar.pack(fill="x")
        char_bar.pack_propagate(False)

        lbl = ctk.CTkLabel(
            char_bar,
            text="0 caracteres",
            font=(Typography.FAMILY, 11),
            text_color=Colors.TEXT_SECONDARY,
            anchor="e",
        )
        lbl.pack(side="right", padx=12)

        def _actualizar(*_):
            n = len(email_text.get("1.0", tk.END)) - 1
            lbl.configure(text=f"{n} caracteres")

        email_text.bind("<KeyRelease>", _actualizar)
        _actualizar()

    def _crear_hint(self, parent):
        hint = ctk.CTkFrame(parent, fg_color=Colors.BACKGROUND, corner_radius=Spacing.RADIUS_SM)
        hint.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(
            hint,
            text="Tip: Usa  Ctrl + Enter  para enviar rapidamente",
            font=(Typography.FAMILY, 11),
            text_color=Colors.TEXT_DISABLED,
            anchor="center",
        ).pack(pady=10)

    def _crear_botones_accion(self):
        actions_outer = ctk.CTkFrame(self, fg_color=Colors.BACKGROUND, corner_radius=0, height=72)
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
            command=self.destroy,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self._btn_enviar = ctk.CTkButton(
            actions,
            text="Enviar Email",
            font=(Typography.FAMILY, 14, Typography.BOLD),
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
            text_color=Colors.HEADER_TEXT,
            corner_radius=Spacing.RADIUS_MD,
            height=44,
            command=self._enviar,
        )
        self._btn_enviar.grid(row=0, column=1, sticky="ew")

        self.bind("<Control-Return>", lambda _: self._enviar())

    # =========================================================
    # Logica de envio
    # =========================================================

    def _enviar(self):
        contenido = self._email_text.get("1.0", tk.END).strip()
        if not contenido:
            messagebox.showerror("Error", "El contenido no puede estar vacio.", parent=self)
            return

        destinatario = self._entry_destinatario.get().strip()
        if not destinatario or "@" not in destinatario or "." not in destinatario.split("@")[-1]:
            msg = "El destinatario no puede estar vacio." if not destinatario else "Formato de email invalido (ej: nombre@dominio.com)"
            self._lbl_error_dest.configure(text=msg)
            self._entry_destinatario.configure(border_color="#DC2626")
            self._entry_destinatario.focus_set()
            return

        self._btn_enviar.configure(state="disabled", text="Enviando...")
        self.update()

        def _tarea():
            try:
                enviar_email_multiperiodo(
                    hotel=self._state.hotel.get(),
                    resultado_multiperiodo=self._state.resultado_multiperiodo,
                    remitente=self.REMITENTE,
                    destinatario=destinatario,
                    texto_override=contenido,
                )
                self.after(0, lambda: (
                    self.destroy(),
                    messagebox.showinfo("OK", "Email enviado correctamente."),
                ))
            except Exception as e:
                self.after(0, lambda: (
                    self._btn_enviar.configure(state="normal", text="Enviar Email"),
                    messagebox.showerror("Error", f"No se pudo enviar:\n{e}", parent=self),
                ))

        threading.Thread(target=_tarea, daemon=True).start()
