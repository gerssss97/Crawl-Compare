"""Modal de historial de comparaciones previas."""

import customtkinter as ctk

from UI.styles import Colors, Typography, Spacing


class HistorialModal(ctk.CTkToplevel):
    def __init__(self, parent, entradas: list, on_restaurar=None, on_limpiar=None):
        super().__init__(parent)
        self._on_restaurar = on_restaurar
        self._on_limpiar = on_limpiar

        self.title("Historial de comparaciones")
        self.geometry("520x480")
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=Colors.SURFACE)

        self._construir(entradas)
        self.after(50, lambda: self._centrar(parent))

    def _construir(self, entradas: list):
        # Body scrollable
        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=Colors.BACKGROUND,
            corner_radius=0,
        )
        scroll.pack(fill="both", expand=True, padx=Spacing.LG, pady=(Spacing.LG, Spacing.SM))
        scroll.columnconfigure(0, weight=1)

        if not entradas:
            ctk.CTkLabel(
                scroll,
                text="No hay comparaciones registradas.",
                font=(Typography.FAMILY, Typography.BODY),
                text_color=Colors.TEXT_SECONDARY,
            ).pack(pady=Spacing.XL)
        else:
            for entrada in entradas:
                self._crear_fila(scroll, entrada)

        # Footer
        footer = ctk.CTkFrame(self, fg_color=Colors.SURFACE, corner_radius=0)
        footer.pack(fill="x", padx=Spacing.LG, pady=(0, Spacing.LG))

        if self._on_limpiar is not None:
            ctk.CTkButton(
                footer,
                text="Limpiar historial",
                font=(Typography.FAMILY, Typography.SMALL),
                fg_color="transparent",
                hover_color=Colors.BORDER,
                text_color=Colors.TEXT_SECONDARY,
                border_width=1,
                border_color=Colors.BORDER,
                corner_radius=Spacing.RADIUS_SM,
                height=32,
                command=self._on_click_limpiar,
            ).pack(side="left")

    def _crear_fila(self, parent, entrada: dict):
        hotel = entrada.get("hotel", "")
        edificio = entrada.get("edificio") or ""
        habitacion = entrada.get("habitacion", "")
        fecha_entrada = entrada.get("fecha_entrada", "")
        fecha_salida = entrada.get("fecha_salida", "")
        adultos = entrada.get("adultos", 1)
        ninos = entrada.get("ninos", 0)
        timestamp = entrada.get("timestamp", "")

        nombre_hotel = f"{hotel} — {edificio}" if edificio else hotel
        linea1 = f"{nombre_hotel}  |  {habitacion}"

        partes_linea2 = []
        if fecha_entrada or fecha_salida:
            partes_linea2.append(f"{fecha_entrada} → {fecha_salida}")
        huesp = f"{adultos} adulto{'s' if adultos != 1 else ''}"
        if ninos:
            huesp += f", {ninos} niño{'s' if ninos != 1 else ''}"
        partes_linea2.append(huesp)
        if timestamp:
            # Mostrar solo la parte de fecha y hora sin microsegundos
            partes_linea2.append(timestamp[:16].replace("T", " "))
        linea2 = "   •   ".join(partes_linea2)

        fila = ctk.CTkFrame(
            parent,
            fg_color=Colors.SURFACE,
            corner_radius=Spacing.RADIUS_SM,
            border_width=1,
            border_color=Colors.BORDER,
            cursor="hand2",
        )
        fila.pack(fill="x", pady=(0, Spacing.XS))
        fila.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            fila,
            text=linea1,
            font=(Typography.FAMILY, Typography.BODY, Typography.BOLD),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 2))

        ctk.CTkLabel(
            fila,
            text=linea2,
            font=(Typography.FAMILY, Typography.SMALL),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=Spacing.MD, pady=(0, Spacing.SM))

        # Bind click en fila y todos sus hijos
        for widget in (fila, *fila.winfo_children()):
            widget.bind("<Button-1>", lambda e, ent=entrada: self._on_click_fila(ent))

    def _on_click_fila(self, entrada: dict):
        if self._on_restaurar:
            self._on_restaurar(entrada)
        self.destroy()

    def _on_click_limpiar(self):
        if self._on_limpiar:
            self._on_limpiar()
        self.destroy()

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
        y = py + (ph - h) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
