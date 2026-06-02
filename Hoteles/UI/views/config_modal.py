"""Modal de configuración con pestañas.

Por ahora sólo "General" muestra contenido real (info del Excel actual).
Las pestañas "Email", "API Keys" y "Scraping" quedan como placeholders
listas para iteraciones futuras.
"""

import re
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from Core.controller import GestorService
from Core.email_templates import DEFAULT_EMAIL_TEMPLATE, EMAIL_TAGS, EMAIL_TAGS_GLOBALES, EMAIL_TAGS_PERIODO
from Core.services.config_service import ConfigService
from UI.components.ctk_text_editor import CTkTextEditor
from UI.styles import Colors, Spacing, Typography


class ConfigModal(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Configuración")
        self.geometry("620x550")
        self.minsize(500, 520)
        self.transient(parent)
        self.grab_set()

        self.configure(fg_color=Colors.SURFACE)
        self._config = ConfigService()

        self.tabview = ctk.CTkTabview(
            self,
            fg_color=Colors.SURFACE,
            text_color=Colors.TEXT_PRIMARY,
            segmented_button_fg_color=Colors.TAB_BAR_BACKGROUND,
            segmented_button_unselected_color=Colors.SECONDARY_DISABLED,
            segmented_button_unselected_hover_color=Colors.SECONDARY,
            segmented_button_selected_color=Colors.PRIMARY_LOWER,
            segmented_button_selected_hover_color=Colors.PRIMARY_LOWER,
        )
        self.tabview.pack(fill="both", expand=True, padx=Spacing.LG, pady=Spacing.SMP)

        self.tabview.add("General")
        self.tabview.add("Email")
        self.tabview.add("API Keys")
        self.tabview.add("Scraping")

        self._construir_tab_general()
        self._construir_tab_email()
        self._construir_tab_placeholder(
            "API Keys",
            "Próximamente: GROQ_API_KEY"
        )
        self._construir_tab_placeholder(
            "Scraping",
            "Próximamente: delays, timeouts, modo headless, etc."
        )

        self.after(50, lambda: self._centrar(parent))

    def _construir_tab_general(self):
        tab = self.tabview.tab("General")

        ctk.CTkLabel(
            tab,
            text="Archivo Excel actual",
            font=(Typography.FAMILY, Typography.BODY, Typography.BOLD),
            anchor="w",
        ).pack(fill="x", padx=Spacing.LG, pady=(Spacing.LG, Spacing.XS))

        path = GestorService.get_current_path()
        texto = path if path else "No hay archivo Excel cargado."

        ctk.CTkLabel(
            tab,
            text=texto,
            font=(Typography.FAMILY, Typography.SMALL),
            text_color=Colors.TEXT_SECONDARY,
            wraplength=520,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=Spacing.LG, pady=(0, Spacing.MD))

        ctk.CTkLabel(
            tab,
            text=(
                "Para cambiar el archivo, cerrá este modal y usá el botón "
                "“Cambiar” de la barra superior."
            ),
            font=(Typography.FAMILY, Typography.SMALL),
            text_color=Colors.TEXT_SECONDARY,
            wraplength=520,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=Spacing.LG, pady=(0, Spacing.LG))

    def _construir_tab_placeholder(self, tab_name: str, mensaje: str):
        tab = self.tabview.tab(tab_name)
        ctk.CTkLabel(
            tab,
            text=mensaje,
            font=(Typography.FAMILY, Typography.BODY),
            text_color=Colors.TEXT_SECONDARY,
            wraplength=520,
            justify="left",
        ).pack(pady=Spacing.XL, padx=Spacing.LG)

    def _construir_tab_email(self):
        _tab = self.tabview.tab("Email")
        scroll = ctk.CTkScrollableFrame(_tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        tab = scroll

        _sb_canvas = scroll._scrollbar._canvas
        _parent_canvas = scroll._parent_canvas

        def _fix_scrollbar_wheel(event):
            _parent_canvas.yview_scroll(int(-event.delta / 6), "units")
            return "break"

        _sb_canvas.bind("<MouseWheel>", _fix_scrollbar_wheel)

        CHIP_FONT_SIZE  = 11   # font size de chips y labels de sección
        CHIP_HEIGHT     = 22   # altura de cada chip
        INPUT_HEIGHT    = 34   # altura de entry y botones de acción
        EDITOR_INSET    = 2    # padding interno del frame del editor

        # ── Firma ──────────────────────────────────────────────────────────
        firma_row = ctk.CTkFrame(tab, fg_color="transparent")
        firma_row.pack(fill="x", padx=Spacing.LG, pady=(0, Spacing.SM))

        ctk.CTkLabel(
            firma_row,
            text="Firma",
            font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
            width=60,
        ).pack(side="left", anchor="n", padx=(0, Spacing.SM))

        firma_frame = ctk.CTkFrame(
            firma_row,
            fg_color=Colors.BACKGROUND,
            corner_radius=Spacing.RADIUS_SM,
            border_width=1,
            border_color=Colors.BORDER,
        )
        firma_frame.pack(side="left", fill="x", expand=True)

        self._entry_firma = CTkTextEditor(
            firma_frame,
            lines=3,
            activate_scrollbars=False,
        )
        self._entry_firma.pack(fill="x", padx=2, pady=2)
        firma_guardada = self._config.get_email_firma()
        if firma_guardada:
            self._entry_firma.insert("1.0", firma_guardada)

        # ── Label template ─────────────────────────────────────────────────
        ctk.CTkLabel(
            tab,
            text="Template del email",
            font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=Spacing.LG, pady=(Spacing.XS, Spacing.XXS))

        # ── Chips fila 1: variables globales ───────────────────────────────
        CHIPS_GLOBALES = [
            ("{hotel}", "hotel"),
            ("{habitacion_excel}", "hab. excel"),
            ("{habitacion_web}", "hab. web"),
            ("{firma}", "firma"),
        ]
        CHIPS_PERIODO = [
            ("{periodo_id}", "periodo id"),
            ("{fecha_inicio_periodo}", "inicio periodo"),
            ("{fecha_fin_periodo}", "fin periodo"),
            ("{fecha_inicio_busqueda}", "inicio búsqueda"),
            ("{fecha_fin_busqueda}", "fin búsqueda"),
            ("{precio_excel}", "precio excel"),
            ("{precio_web}", "precio web"),
            ("{diferencia}", "diferencia"),
            ("{estado}", "estado"),
        ]

        def _fila_con_label(parent, label_text):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=Spacing.LG, pady=(0, EDITOR_INSET))
            ctk.CTkLabel(
                row,
                text=label_text,
                font=(Typography.FAMILY, CHIP_FONT_SIZE),
                text_color=Colors.TEXT_SECONDARY,
                anchor="w",
            ).pack(side="left", anchor="n", padx=(0, Spacing.XS))
            return row

        def _chip_normal(token, label):
            return dict(
                text=label,
                font=(Typography.FAMILY, CHIP_FONT_SIZE),
                fg_color=Colors.PRIMARY_LIGHT,
                hover_color=Colors.SECONDARY_DISABLED,
                text_color=Colors.PRIMARY,
                border_width=1,
                border_color=Colors.SECONDARY,
                corner_radius=Spacing.RADIUS_SM,
                height=CHIP_HEIGHT,
                width=0,
                command=lambda t=token: self._insertar_variable(t),
            )

        def _seccion_chips(parent, label_text, chips, spacing3=4):
            row = _fila_con_label(parent, label_text)

            _probe = ctk.CTkButton(row, **_chip_normal("", ""))
            _probe.update_idletasks()
            _chip_h = _probe.winfo_reqheight()
            _probe.destroy()
            chip_font = tk.font.Font(size=_chip_h)

            container = tk.Text(
                row,
                wrap="word",
                cursor="arrow",
                state="normal",
                relief="flat",
                bd=0,
                height=1,
                font=chip_font,
                bg=Colors.SURFACE,
                highlightthickness=0,
                padx=0,
                pady=0,
                spacing3=spacing3,
            )
            container.pack(side="left", fill="x", expand=True)

            for token, label in chips:
                btn = ctk.CTkButton(container, **_chip_normal(token, label))
                container.window_create("end", window=btn, padx=4, pady=0)
                container.insert("end", "​")

            container.configure(state="disabled")

            def _recalcular(c=container):
                c.configure(state="normal")
                lineas = c.count("1.0", "end", "displaylines")[0]
                c.configure(height=max(1, lineas), state="disabled")

            def _ajustar_altura(_=None, c=container):
                c.after(20, lambda: _recalcular(c))

            container.bind("<Configure>", _ajustar_altura)
            container.after(100, lambda: _recalcular(container))
            container.after(300, lambda: _recalcular(container))

        _seccion_chips(tab, "Globales:", CHIPS_GLOBALES)
        _seccion_chips(tab, "Solo en for:", CHIPS_PERIODO, spacing3=2)

        row_for = _fila_con_label(tab, "Bloque:")
        ctk.CTkButton(
            row_for,
            text="{% for periodo %} ... {% end %}",
            font=(Typography.MONO, CHIP_FONT_SIZE),
            fg_color=Colors.SURFACE,
            hover_color=Colors.BACKGROUND,
            text_color=Colors.TEXT_PRIMARY,
            border_width=1,
            border_color=Colors.BORDER,
            corner_radius=Spacing.RADIUS_SM,
            height=CHIP_HEIGHT,
            width=0,
            command=lambda: self._insertar_variable("{% for periodo %}\n\n{% end %}"),
        ).pack(side="left")

        # ── Editor ─────────────────────────────────────────────────────────
        editor_frame = ctk.CTkFrame(
            tab,
            fg_color=Colors.BACKGROUND,
            corner_radius=Spacing.RADIUS_SM,
            border_width=1,
            border_color=Colors.BORDER,
        )
        editor_frame.pack(fill="x", padx=Spacing.LG, pady=(Spacing.XS, EDITOR_INSET))

        def _resolver_tags(texto_hasta_cursor: str) -> list[str]:
            dentro = texto_hasta_cursor.count("{% for periodo %}") > texto_hasta_cursor.count("{% end %}")
            return EMAIL_TAGS_PERIODO if dentro else EMAIL_TAGS_GLOBALES

        self._textbox_template = CTkTextEditor(
            editor_frame,
            lines=10,
            auto_grow=True,
            autocomplete_options=EMAIL_TAGS,
            context_resolver=_resolver_tags,
        )
        self._textbox_template.pack(fill="x", padx=EDITOR_INSET, pady=EDITOR_INSET)

        template_guardado = self._config.get_email_template()
        self._textbox_template.insert("1.0", template_guardado or DEFAULT_EMAIL_TEMPLATE)

        # ── Hint ───────────────────────────────────────────────────────────
        ctk.CTkLabel(
            tab,
            text="Tip: dejá el área vacía para usar el template predeterminado del sistema.",
            font=(Typography.FAMILY, CHIP_FONT_SIZE),
            text_color=Colors.TEXT_DISABLED,
            anchor="w",
        ).pack(fill="x", padx=Spacing.LG, pady=(0, Spacing.XS))

        # ── Botones ────────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.pack(fill="x", padx=Spacing.LG, pady=(0, Spacing.LG))
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            btn_row,
            text="Restaurar predeterminado",
            font=(Typography.FAMILY, Typography.SMALL),
            fg_color=Colors.SURFACE,
            hover_color=Colors.BACKGROUND,
            text_color=Colors.TEXT_SECONDARY,
            border_width=1,
            border_color=Colors.BORDER,
            corner_radius=Spacing.RADIUS_SM,
            height=INPUT_HEIGHT,
            command=self._restaurar_template,
        ).grid(row=0, column=0, sticky="ew", padx=(0, Spacing.SM))

        ctk.CTkButton(
            btn_row,
            text="Guardar",
            font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
            text_color=Colors.HEADER_TEXT,
            corner_radius=Spacing.RADIUS_SM,
            height=INPUT_HEIGHT,
            command=self._guardar_email_config,
        ).grid(row=0, column=1, sticky="ew")

    def _insertar_variable(self, token: str):
        try:
            pos = self._textbox_template._textbox.index(tk.INSERT)
            self._textbox_template._textbox.insert(pos, token)
        except Exception:
            self._textbox_template.insert(tk.END, token)
        self._textbox_template.focus_set()

    def _validar_template(self, template: str) -> str | None:
        VARS_GLOBALES = {"hotel", "habitacion_excel", "habitacion_web", "firma"}
        VARS_PERIODO  = {
            "periodo_id", "fecha_inicio_periodo", "fecha_fin_periodo",
            "fecha_inicio_busqueda", "fecha_fin_busqueda",
            "precio_excel", "precio_web", "diferencia", "estado",
        }
        TAG_FOR = "{% for periodo %}"
        TAG_END = "{% end %}"

        count_for = template.count(TAG_FOR)
        count_end = template.count(TAG_END)

        if count_for != count_end or count_for > 1:
            return (
                "Bloque mal formado: cada '{% for periodo %}' necesita exactamente un '{% end %}', "
                "y solo puede haber un bloque."
            )

        tiene_bloque = count_for == 1

        if tiene_bloque:
            exterior = template.replace(template.split(TAG_FOR)[1].split(TAG_END)[0], "")
            exterior = exterior.replace(TAG_FOR, "").replace(TAG_END, "")
        else:
            exterior = template

        tokens_exterior = set(re.findall(r"\{(\w+)\}", exterior))
        fuera_de_lugar = tokens_exterior & VARS_PERIODO
        if fuera_de_lugar:
            lista = ", ".join(f"{{{v}}}" for v in sorted(fuera_de_lugar))
            return (
                f"Las siguientes variables solo pueden usarse dentro del bloque "
                f"{{% for periodo %}}...{{% end %}}:\n{lista}"
            )

        todos_tokens = set(re.findall(r"\{(\w+)\}", template))
        desconocidas = todos_tokens - VARS_GLOBALES - VARS_PERIODO
        if desconocidas:
            lista = ", ".join(f"{{{v}}}" for v in sorted(desconocidas))
            return f"Variable(s) desconocida(s): {lista}\nCorregí el nombre antes de guardar."

        return None

    def _guardar_email_config(self):
        firma    = self._entry_firma.get("1.0", tk.END).strip()
        template = self._textbox_template.get("1.0", tk.END).strip()

        if template:
            error = self._validar_template(template)
            if error:
                messagebox.showerror("Error en el template", error, parent=self)
                return

        self._config.set_email_firma(firma or None)
        self._config.set_email_template(template or None)
        messagebox.showinfo("Guardado", "Configuración de email guardada.", parent=self)

    def _restaurar_template(self):
        if messagebox.askyesno(
            "Restaurar",
            "¿Restaurar el template predeterminado?\nSe perderá el template actual.",
            parent=self,
        ):
            self._textbox_template.delete("1.0", tk.END)
            self._textbox_template.insert("1.0", DEFAULT_EMAIL_TEMPLATE)
            self._config.set_email_template(None)

    def _centrar(self, parent):
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
        x = px + (pw - w) // 2
        y = py + (ph - h) // 3
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
