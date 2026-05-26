"""Dropdown personalizado que funciona correctamente con CTk."""

import tkinter as tk
import customtkinter as ctk
from UI.styles import Colors, Typography, Spacing


class CTkCustomDropdown(ctk.CTkFrame):
    """Dropdown personalizado que realmente llena el ancho y es clickeable.

    Solución workaround para las limitaciones de CTkComboBox:
    - Llena 100% del ancho del dropdown
    - Se puede clickear en cualquier parte para abrir
    - No permite editar el texto
    - Soporta typeahead: tipear ≥2 letras filtra las opciones con debounce de 500ms
    """

    def __init__(self, parent, values=None, textvariable=None, command=None, on_confirm=None, placeholder_text="Seleccionar...", width=None, max_visible=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.values = values or []
        self.textvariable = textvariable
        self.command = command
        self._placeholder_text = placeholder_text
        self._dropdown_open = False
        self._dropdown_window = None
        self._fixed_width = width
        self._max_visible = max_visible
        self._bind_ids = {}  # event → binding ID para desvinculación selectiva

        # --- Typeahead state ---
        self._search_mode = False
        self._after_id = None
        self._prev_value = ""  # para restaurar con Escape
        self.on_confirm = on_confirm
        self._just_selected = False  # bloquea _activar_modo_busqueda durante 200ms: el <Button-1> que cerró el Toplevel se propaga al display_label recién visible y lo reabre sin este guard

        # --- Keyboard navigation state ---
        self._hovered_index = -1       # índice activo en el popup (-1 = ninguno)
        self._dropdown_buttons = []    # referencias a los CTkButton del popup
        self._dropdown_values = []     # valores paralelos a _dropdown_buttons

        # Frame principal con entrada y botón
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="x" if width is None else "none")

        # Frame que simula un entry (sin canvas interno que cause redibujados)
        self.entry = ctk.CTkFrame(
            self.main_frame,
            fg_color=Colors.SURFACE,
            border_color=Colors.BORDER,
            corner_radius=Spacing.RADIUS_MD,
            border_width=1,
            height=40,
            cursor="hand2",
        )
        if width is not None:
            entry_width = width - 40 - Spacing.XXS
            self.entry.configure(width=entry_width)
            self.entry.pack(side="left", padx=(0, Spacing.XXS))
            self.entry.pack_propagate(False)
        else:
            self.entry.pack(side="left", fill="x", expand=True, padx=(0, Spacing.XXS))
            self.entry.pack_propagate(False)

        self._display_label = ctk.CTkLabel(
            self.entry,
            text=placeholder_text,
            font=(Typography.FAMILY, Typography.BODY),
            text_color=Colors.TEXT_DISABLED,
            fg_color="transparent",
            anchor="w",
            height=36,
        )
        self._display_label.pack(fill="x", padx=(Spacing.SM, Spacing.SM), pady=2)

        # Entry de búsqueda (oculto al inicio, se muestra en modo búsqueda)
        self._search_entry = ctk.CTkEntry(
            self.entry,
            fg_color="transparent",
            border_width=0,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text="Buscar...",
            placeholder_text_color=Colors.TEXT_DISABLED,
            font=(Typography.FAMILY, Typography.BODY),
            height=36,
        )
        self._search_entry.bind("<KeyRelease>", self._on_search_changed)
        self._search_entry.bind("<Escape>", lambda _: self._cancelar_busqueda())
        self._search_entry.bind("<Return>", self._on_search_enter)
        self._search_entry.bind("<Up>",   self._on_key_up)
        self._search_entry.bind("<Down>", self._on_key_down)

        # Botón dropdown
        self.button = ctk.CTkButton(
            self.main_frame,
            text="▼",
            width=40,
            height=40,
            fg_color=Colors.BORDER,
            hover_color=Colors.PRIMARY_LIGHT,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=Spacing.RADIUS_MD,
            command=self._on_button_click,
        )
        self.button.pack(side="right", padx=(Spacing.XXS, 0))

        # Click en el entry activa el modo búsqueda (FocusIn excluido: el foco
        # puede llegar programáticamente desde on_confirm y abriría el dropdown sin acción del usuario)
        self.entry.bind("<Button-1>", lambda _: self._activar_modo_busqueda(), add="+")
        self._display_label.bind("<Button-1>", lambda _: self._activar_modo_busqueda(), add="+")

        # Sincronizar el entry cuando la StringVar cambia externamente
        if self.textvariable:
            self.textvariable.trace_add("write", self._on_textvariable_changed)

    # ------------------------------------------------------------------ #
    #  Typeahead                                                           #
    # ------------------------------------------------------------------ #

    def _activar_modo_busqueda(self):
        if self._search_mode or self._just_selected:
            return
        self._prev_value = self.get()
        self._search_mode = True
        self._display_label.pack_forget()
        self._search_entry.pack(fill="x", padx=(Spacing.SM, Spacing.SM), pady=2)
        self._search_entry.delete(0, "end")
        self._search_entry.focus_set()
        self._open_dropdown(values=self.values)

    def _cancel_pending_search(self):
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None

    def _desactivar_modo_busqueda(self, restore=False):
        self._search_mode = False
        self._cancel_pending_search()
        self._search_entry.pack_forget()
        self._display_label.pack(fill="x", padx=(Spacing.SM, Spacing.SM), pady=2)
        if restore:
            self._set_display(self._prev_value)
            if self.textvariable:
                self.textvariable.set(self._prev_value)

    def _cancelar_busqueda(self):
        self._close_dropdown()
        self._desactivar_modo_busqueda(restore=True)

    def _on_search_changed(self, event):
        # Ignorar teclas de navegación que no cambian el texto
        if event.keysym in ("Escape", "Return", "Up", "Down", "Tab"):
            return
        self._cancel_pending_search()
        self._after_id = self.after(500, self._ejecutar_busqueda)

    def _on_search_enter(self, event):
        """Selecciona el item con hover activo, o el primero si ninguno está resaltado."""
        if self._hovered_index >= 0 and self._hovered_index < len(self._dropdown_values):
            value = self._dropdown_values[self._hovered_index]
        else:
            query = self._search_entry.get().strip()
            filtrados = [v for v in self.values if query.lower() in v.lower()] if query else self.values
            if not filtrados:
                return
            value = filtrados[0]
        self._select_option(value)
        if self.on_confirm:
            self.on_confirm()

    def _on_key_down(self, event):
        if not self._dropdown_open or not self._dropdown_buttons:
            return
        new_index = min(self._hovered_index + 1, len(self._dropdown_buttons) - 1)
        self._set_hover(new_index)

    def _on_key_up(self, event):
        if not self._dropdown_open or not self._dropdown_buttons:
            return
        new_index = max(self._hovered_index - 1, 0)
        self._set_hover(new_index)

    def _set_hover(self, index):
        """Aplica el highlight al botón en `index` y quita el anterior."""
        if self._hovered_index >= 0 and self._hovered_index < len(self._dropdown_buttons):
            self._dropdown_buttons[self._hovered_index].configure(fg_color=Colors.SUCCESS_LIGHT)
        self._hovered_index = index
        if index >= 0 and index < len(self._dropdown_buttons):
            self._dropdown_buttons[index].configure(fg_color=Colors.PRIMARY_LIGHT)
            self._scroll_to_index(index)

    def _clear_hover(self, index):
        """Quita el highlight del botón si el mouse lo deja y no hay navegación por teclado activa."""
        if self._hovered_index == index:
            self._dropdown_buttons[index].configure(fg_color=Colors.SUCCESS_LIGHT)
            self._hovered_index = -1

    def _scroll_to_index(self, index):
        """Scrollea el CTkScrollableFrame para que el botón en `index` sea visible."""
        if self._dropdown_window is None:
            return
        # CTkScrollableFrame expone _parent_canvas con el canvas interno
        scroll_frames = [
            w for w in self._dropdown_window.winfo_children()
            if isinstance(w, ctk.CTkScrollableFrame)
        ]
        if not scroll_frames:
            return
        scroll_frame = scroll_frames[0]
        canvas = scroll_frame._parent_canvas

        canvas.update_idletasks()
        total_height = canvas.bbox("all")
        if not total_height:
            return
        total_height = total_height[3]
        if total_height == 0:
            return

        btn = self._dropdown_buttons[index]
        btn.update_idletasks()
        btn_y = btn.winfo_y()
        btn_h = btn.winfo_height()
        canvas_h = canvas.winfo_height()

        # Fracción [0,1] del top e bottom del botón sobre el contenido total
        top_frac    = btn_y / total_height
        bottom_frac = (btn_y + btn_h) / total_height

        # Posición actual del viewport
        view_top, view_bottom = canvas.yview()

        if top_frac < view_top:
            canvas.yview_moveto(top_frac)
        elif bottom_frac > view_bottom:
            canvas.yview_moveto(bottom_frac - (canvas_h / total_height))

    def _ejecutar_busqueda(self):
        self._after_id = None
        query = self._search_entry.get().strip()
        filtrados = [v for v in self.values if query.lower() in v.lower()] if query else self.values
        self._close_dropdown()
        if filtrados:
            self._open_dropdown(values=filtrados)
        else:
            self._open_dropdown_sin_resultados()

    def _open_dropdown_mensaje(self, texto):
        """Abre un popup con un único label de mensaje (no seleccionable)."""
        self._dropdown_open = True
        self.update_idletasks()

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 2
        width_px = self.winfo_width()

        self._dropdown_window = tk.Toplevel(self.winfo_toplevel())
        self._dropdown_window.wm_overrideredirect(True)
        self._dropdown_window.resizable(False, False)
        self._dropdown_window.configure(background=Colors.BACKGROUND)
        self._dropdown_window.geometry(f"{width_px}x1+-9999+-9999")

        frame = ctk.CTkFrame(
            self._dropdown_window,
            fg_color=Colors.BACKGROUND,
        )
        frame.pack(fill="both", expand=True)

        label = ctk.CTkLabel(
            frame,
            text=texto,
            font=(Typography.FAMILY, Typography.BODY),
            text_color=Colors.TEXT_DISABLED,
            fg_color="transparent",
            anchor="w",
        )
        label.pack(fill="x", padx=Spacing.SM, pady=Spacing.SM)

        self._dropdown_window.update_idletasks()
        height_px = frame.winfo_reqheight() + 4
        self._dropdown_window.geometry(f"{width_px}x{height_px}+{x}+{y}")

        root = self.winfo_toplevel()
        self._bind_ids["<Button-1>"] = root.bind("<Button-1>", self._on_click_outside, add="+")
        self._bind_ids["<Unmap>"] = root.bind("<Unmap>", lambda _: self._close_dropdown(), add="+")

    def _open_dropdown_sin_resultados(self):
        self._open_dropdown_mensaje("Sin resultados")

    # ------------------------------------------------------------------ #
    #  Helpers de display                                                  #
    # ------------------------------------------------------------------ #

    def _on_button_click(self):
        """El botón ▼ abre el popup normal con TODOS los valores."""
        if self._search_mode:
            self._desactivar_modo_busqueda()
        self._toggle_dropdown()

    def _on_textvariable_changed(self, *args):
        value = self.textvariable.get()
        self._set_display(value)

    def _truncate_text(self, text, available_px=None, font=None):
        """Trunca el texto con '…' para que entre en el ancho dado (o el entry si no se pasa)."""
        import tkinter.font as tkfont

        if available_px is None:
            self.entry.update_idletasks()
            available_px = self.entry.winfo_width() - (Spacing.SM * 2)

        if available_px <= 0:
            return text

        if font is None:
            font = tkfont.Font(family=Typography.FAMILY, size=Typography.BODY)

        if font.measure(text) <= available_px:
            return text

        for i in range(len(text), 0, -1):
            truncated = text[:i] + "…"
            if font.measure(truncated) <= available_px:
                return truncated

        return "…"

    def _set_display(self, value):
        """Actualiza el label de display con el valor o el placeholder."""
        if value:
            display_text = self._truncate_text(value)
            self._display_label.configure(text=display_text, text_color=Colors.TEXT_PRIMARY)
        else:
            self._display_label.configure(text=self._placeholder_text, text_color=Colors.TEXT_DISABLED)

    # ------------------------------------------------------------------ #
    #  Popup principal                                                     #
    # ------------------------------------------------------------------ #

    def _toggle_dropdown(self):
        if self._dropdown_open:
            self._close_dropdown()
        else:
            self._open_dropdown()

    def _open_dropdown(self, values=None):
        if self._dropdown_open:
            return

        display_values = values if values is not None else self.values

        # Resetear estado de navegación por teclado
        self._hovered_index = -1
        self._dropdown_buttons = []
        self._dropdown_values = list(display_values)

        self._dropdown_open = True
        self.update_idletasks()

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 2

        width_px = self.winfo_width()
        self._dropdown_window = tk.Toplevel(self.winfo_toplevel())
        self._dropdown_window.wm_overrideredirect(True)
        self._dropdown_window.resizable(False, False)
        self._dropdown_window.configure(background=Colors.BACKGROUND)
        self._dropdown_window.geometry(f"{width_px}x1+-9999+-9999")

        scroll_frame = ctk.CTkScrollableFrame(
            self._dropdown_window,
            fg_color=Colors.BACKGROUND,
            scrollbar_button_color=Colors.BORDER,
            scrollbar_button_hover_color=Colors.PRIMARY,
        )
        scroll_frame.pack(fill="both", expand=True)

        long_text = "X" * 200
        probe_btn = ctk.CTkButton(scroll_frame, text=long_text, anchor="w")
        probe_btn.pack(fill="x")
        self._dropdown_window.geometry(f"{width_px}x100+-9999+-9999")
        self._dropdown_window.update_idletasks()

        import tkinter.font as tkfont
        real_font_str = probe_btn._text_label.cget("font")
        parts = real_font_str.split()
        font_family = parts[0] if parts else Typography.FAMILY
        font_size = int(parts[1]) if len(parts) > 1 else Typography.BODY
        real_font = tkfont.Font(family=font_family, size=font_size)

        list_available_px = probe_btn._text_label.winfo_width()
        probe_btn.destroy()

        for idx, value in enumerate(display_values):
            display = self._truncate_text(value, available_px=list_available_px, font=real_font)
            btn = ctk.CTkButton(
                scroll_frame,
                text=display,
                fg_color=Colors.SUCCESS_LIGHT,
                hover_color=Colors.SUCCESS_LIGHT,  # desactivamos el hover nativo de CTk
                text_color=Colors.TEXT_PRIMARY,
                anchor="w",
                command=lambda v=value: self._select_option(v),
            )
            btn.pack(fill="x", pady=2)
            self._dropdown_buttons.append(btn)
            # Hover de mouse: sincroniza _hovered_index con el cursor
            btn.bind("<Enter>", lambda _e, i=idx: self._set_hover(i),  add="+")
            btn.bind("<Leave>", lambda _e, i=idx: self._clear_hover(i), add="+")

        self._dropdown_window.update_idletasks()

        children = scroll_frame.winfo_children()
        content_height_px = sum(c.winfo_reqheight() + 4 for c in children)

        parent_canvas = scroll_frame._parent_canvas
        parent_frame = scroll_frame._parent_frame
        overhead = parent_frame.winfo_reqheight() - parent_canvas.winfo_reqheight()
        if overhead <= 0:
            overhead = 18

        if self._max_visible and len(children) > self._max_visible:
            max_content_px = sum(c.winfo_reqheight() + 4 for c in children[:self._max_visible])
            max_height_px = max_content_px + overhead
        else:
            max_height_px = content_height_px + overhead
        height_px_final = min(content_height_px + overhead, max_height_px)

        self._dropdown_window.geometry(f"{width_px}x{height_px_final}+{x}+{y}")

        root = self.winfo_toplevel()
        self._bind_ids["<Button-1>"] = root.bind("<Button-1>", self._on_click_outside, add="+")
        self._bind_ids["<MouseWheel>"] = root.bind("<MouseWheel>", self._on_scroll_outside, add="+")
        self._bind_ids["<Button-4>"] = root.bind("<Button-4>", self._on_scroll_outside, add="+")
        self._bind_ids["<Button-5>"] = root.bind("<Button-5>", self._on_scroll_outside, add="+")
        self._bind_ids["<Unmap>"] = root.bind("<Unmap>", lambda _: self._close_dropdown(), add="+")

    def _event_inside_popup(self, event) -> bool:
        win = self._dropdown_window
        wx, wy = win.winfo_rootx(), win.winfo_rooty()
        ww, wh = win.winfo_width(), win.winfo_height()
        return wx <= event.x_root <= wx + ww and wy <= event.y_root <= wy + wh

    def _on_click_outside(self, event):
        """Cierra el dropdown (y el modo búsqueda) si el click fue fuera."""
        if self._dropdown_window is None:
            return
        if not self._event_inside_popup(event):
            self._close_dropdown()
            if self._search_mode:
                self._desactivar_modo_busqueda(restore=True)

    def _on_scroll_outside(self, event):
        """Cierra el dropdown si el scroll ocurrió fuera de la ventana del dropdown."""
        if self._dropdown_window is None:
            return
        if not self._event_inside_popup(event):
            self._close_dropdown()

    def _close_dropdown(self):
        root = self.winfo_toplevel()
        for event, bid in self._bind_ids.items():
            root.unbind(event, bid)
        self._bind_ids.clear()
        if self._dropdown_window:
            self._dropdown_window.destroy()
            self._dropdown_window = None
        self._dropdown_open = False
        self._hovered_index = -1
        self._dropdown_buttons = []
        self._dropdown_values = []

    def _select_option(self, value):
        self._just_selected = True
        self.after(200, lambda: setattr(self, "_just_selected", False))
        self._close_dropdown()
        if self._search_mode:
            self._desactivar_modo_busqueda()
        self._set_display(value)
        if self.textvariable:
            self.textvariable.set(value)
        if self.command:
            self.command(value)

    # ------------------------------------------------------------------ #
    #  API pública                                                         #
    # ------------------------------------------------------------------ #

    def set_values(self, values):
        self.values = values

    def get(self):
        text = self._display_label.cget("text")
        return "" if text == self._placeholder_text else text

    def set(self, value):
        self._set_display(value)
        if self.textvariable:
            self.textvariable.set(value)

    def configure(self, **kwargs):
        if "command" in kwargs:
            self.command = kwargs.pop("command")
        if "on_confirm" in kwargs:
            self.on_confirm = kwargs.pop("on_confirm")
        if "values" in kwargs:
            self.set_values(kwargs.pop("values"))
        if kwargs:
            super().configure(**kwargs)
