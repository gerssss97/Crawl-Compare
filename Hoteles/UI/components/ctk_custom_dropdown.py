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
    """

    def __init__(self, parent, values=None, textvariable=None, command=None, placeholder_text="Seleccionar...", width=None, max_visible=None, **kwargs):
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

        self.entry.bind("<Button-1>", lambda _: self._toggle_dropdown(), add="+")
        self._display_label.bind("<Button-1>", lambda _: self._toggle_dropdown(), add="+")

        # Sincronizar el entry cuando la StringVar cambia externamente
        if self.textvariable:
            self.textvariable.trace_add("write", self._on_textvariable_changed)

    def _on_button_click(self):
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

    def _toggle_dropdown(self):
        if self._dropdown_open:
            self._close_dropdown()
        else:
            self._open_dropdown()

    def _open_dropdown(self):
        if self._dropdown_open:
            return

        self._dropdown_open = True
        self.update_idletasks()

        # Coordenadas absolutas de pantalla para posicionar el Toplevel
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 2

        # winfo_width() devuelve píxeles reales. tk.Toplevel geometry() también trabaja
        # en píxeles reales (sin scaling de CTk), así que lo usamos directamente.
        width_px = self.winfo_width()
        # tk.Toplevel en vez de CTkToplevel: evita el minsize 200x200 que CTkToplevel impone
        self._dropdown_window = tk.Toplevel(self.winfo_toplevel())
        self._dropdown_window.wm_overrideredirect(True)
        self._dropdown_window.resizable(False, False)  # evita que winfo_reqheight expanda la ventana
        self._dropdown_window.configure(background=Colors.SUCCESS_LIGHT)
        # Geometría inicial off-screen para medir contenido sin flash visible
        self._dropdown_window.geometry(f"{width_px}x1+-9999+-9999")

        scroll_frame = ctk.CTkScrollableFrame(
            self._dropdown_window,
            fg_color=Colors.BACKGROUND,
            scrollbar_button_color=Colors.BORDER,
            scrollbar_button_hover_color=Colors.PRIMARY,
        )
        scroll_frame.pack(fill="both", expand=True)

        # --- Paso previo: medir el ancho real disponible para texto ---
        # Crear un botón sonda con texto largo para que el _text_label se expanda,
        # layoutear off-screen, medir el padding real del CTkButton, destruir.
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

        # --- Crear botones con texto ya truncado ---
        for value in self.values:
            display = self._truncate_text(value, available_px=list_available_px, font=real_font)
            btn = ctk.CTkButton(
                scroll_frame,
                text=display,
                fg_color=Colors.SUCCESS_LIGHT,
                hover_color=Colors.PRIMARY_LIGHT,
                text_color=Colors.TEXT_PRIMARY,
                anchor="w",
                command=lambda v=value: self._select_option(v),
            )
            btn.pack(fill="x", pady=2)

        # Medir overhead del CTkScrollableFrame midiendo los hijos directamente.
        # No usar ventana - canvas porque con pocos items el canvas no llena la ventana.
        self._dropdown_window.update_idletasks()

        children = scroll_frame.winfo_children()
        content_height_px = sum(c.winfo_reqheight() + 4 for c in children)  # +4 = pady=2 arriba y abajo

        # Overhead: estructura interna del CTkScrollableFrame (corner_radius, padding)
        # Se mide como la diferencia entre _parent_frame y _parent_canvas en reqheight
        parent_canvas = scroll_frame._parent_canvas
        parent_frame = scroll_frame._parent_frame
        overhead = parent_frame.winfo_reqheight() - parent_canvas.winfo_reqheight()
        # Fallback por si la medición da negativo o cero (aún no layouteado)
        if overhead <= 0:
            overhead = 18

        if self._max_visible and len(children) > self._max_visible:
            max_content_px = sum(c.winfo_reqheight() + 4 for c in children[:self._max_visible])
            max_height_px = max_content_px + overhead
        else:
            max_height_px = content_height_px + overhead
        height_px_final = min(content_height_px + overhead, max_height_px)

        # Paso 4: posicionar en la ubicación real
        self._dropdown_window.geometry(f"{width_px}x{height_px_final}+{x}+{y}")

        # Cerrar al hacer click o scroll fuera del dropdown (no con FocusOut, que se
        # dispara inmediatamente cuando el botón roba el foco cerrando el dropdown).
        # Se guardan los IDs para desvinculación selectiva (no borrar bindings de otros dropdowns).
        root = self.winfo_toplevel()
        self._bind_ids["<Button-1>"] = root.bind("<Button-1>", self._on_click_outside, add="+")
        self._bind_ids["<MouseWheel>"] = root.bind("<MouseWheel>", self._on_scroll_outside, add="+")
        self._bind_ids["<Button-4>"] = root.bind("<Button-4>", self._on_scroll_outside, add="+")
        self._bind_ids["<Button-5>"] = root.bind("<Button-5>", self._on_scroll_outside, add="+")
        self._bind_ids["<Unmap>"] = root.bind("<Unmap>", lambda _: self._close_dropdown(), add="+")

    def _on_click_outside(self, event):
        """Cierra el dropdown si el click fue fuera de la ventana del dropdown."""
        if self._dropdown_window is None:
            return
        win = self._dropdown_window
        wx, wy = win.winfo_rootx(), win.winfo_rooty()
        ww, wh = win.winfo_width(), win.winfo_height()
        if not (wx <= event.x_root <= wx + ww and wy <= event.y_root <= wy + wh):
            self._close_dropdown()

    def _on_scroll_outside(self, event):
        """Cierra el dropdown si el scroll ocurrió fuera de la ventana del dropdown."""
        if self._dropdown_window is None:
            return
        win = self._dropdown_window
        wx, wy = win.winfo_rootx(), win.winfo_rooty()
        ww, wh = win.winfo_width(), win.winfo_height()
        if not (wx <= event.x_root <= wx + ww and wy <= event.y_root <= wy + wh):
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

    def _select_option(self, value):
        self._close_dropdown()
        if self.textvariable:
            self.textvariable.set(value)  # dispara _on_textvariable_changed → _set_display
        else:
            self._set_display(value)
        if self.command:
            self.command(value)

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
        if "values" in kwargs:
            self.set_values(kwargs.pop("values"))
        if kwargs:
            super().configure(**kwargs)