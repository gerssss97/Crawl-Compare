"""Modal de configuración con pestañas.

Por ahora sólo "General" muestra contenido real (info del Excel actual).
Las pestañas "Email", "API Keys" y "Scraping" quedan como placeholders
listas para iteraciones futuras.
"""

import customtkinter as ctk

from Core.controller import GestorService
from UI.styles import Colors, Spacing, Typography


class ConfigModal(ctk.CTkToplevel):
    def __init__(self, parent, config_service):
        super().__init__(parent)
        self.config_service = config_service

        self.title("Configuración")
        self.geometry("600x420")
        self.transient(parent)
        self.grab_set()

        self.configure(fg_color=Colors.SURFACE)

        self.tabview = ctk.CTkTabview(
            self,
            fg_color=Colors.SURFACE,
            text_color=Colors.TEXT_PRIMARY,
            segmented_button_fg_color=Colors.BORDER,
            segmented_button_unselected_color=Colors.SECONDARY_DISABLED,
            segmented_button_unselected_hover_color=Colors.SECONDARY,
            segmented_button_selected_color=Colors.PRIMARY,
            segmented_button_selected_hover_color=Colors.PRIMARY_HOVER,
        )
        self.tabview.pack(fill="both", expand=True, padx=Spacing.LG, pady=Spacing.LG)

        self.tabview.add("General")
        self.tabview.add("Email")
        self.tabview.add("API Keys")
        self.tabview.add("Scraping")

        self._construir_tab_general()
        self._construir_tab_placeholder(
            "Email",
            "Próximamente: configuración del email del usuario (remitente, destinatario)."
        )
        self._construir_tab_placeholder(
            "API Keys",
            "Próximamente: GROQ_API_KEY, GMTP_KEY y otras claves."
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

        ctk.CTkLabel(
            tab,
            text=f"Configuración guardada en:\n{self.config_service.path}",
            font=(Typography.FAMILY, Typography.SMALL),
            text_color=Colors.TEXT_DISABLED,
            wraplength=520,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=Spacing.LG, pady=(Spacing.MD, 0))

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
