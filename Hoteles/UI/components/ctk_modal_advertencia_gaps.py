"""Modal CTk de advertencia para gaps (cobertura parcial de periodos)."""

import customtkinter as ctk


class CtkModalAdvertenciaGaps(ctk.CTkToplevel):
    """Modal que advierte sobre gaps antes de ejecutar comparación.

    Muestra qué rangos NO tienen cobertura Excel y permite al usuario
    decidir si continuar de todas formas o cancelar.

    Args:
        parent: Widget padre (ventana principal)
        gap_analysis: GapAnalysis con gaps detectados
        callback: Función que recibe (True=continuar, False=cancelar)
    """

    def __init__(self, parent, gap_analysis, callback):
        super().__init__(parent)
        self.gap_analysis = gap_analysis
        self.callback = callback

        self.title("Advertencia: Cobertura Parcial")
        self.geometry("520x380")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._setup_ui()

        # Centrar respecto al parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

        self.bind('<Escape>', lambda e: self._close(False))

    def _setup_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="#FFF3CD", corner_radius=0, height=60)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        ctk.CTkLabel(
            header,
            text="⚠️  ADVERTENCIA: Cobertura Parcial de Precios",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#856404",
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Contenido
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=15)
        content.grid_rowconfigure(1, weight=1)
        content.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            content,
            text="No hay periodos Excel para los siguientes rangos:",
            font=ctk.CTkFont(size=11),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 8))

        # Caja de texto con gaps
        gaps_text = ctk.CTkTextbox(
            content,
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color=("#F5F5F5", "#2B2B2B"),
            text_color=("#D32F2F", "#FF6B6B"),
            wrap="word",
            state="normal",
        )
        gaps_text.grid(row=1, column=0, sticky="nsew", pady=(0, 10))

        descripcion = self.gap_analysis.get_gap_description()
        gaps_text.insert("1.0", descripcion)
        gaps_text.configure(state="disabled")

        ctk.CTkLabel(
            content,
            text="Se comparará solamente en los periodos con cobertura disponible.",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w",
            wraplength=460,
        ).grid(row=2, column=0, sticky="ew")

        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 15))

        ctk.CTkButton(
            btn_frame,
            text="Continuar de Todas Formas",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2196F3",
            hover_color="#1976D2",
            command=lambda: self._close(True),
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            font=ctk.CTkFont(size=11),
            fg_color="#757575",
            hover_color="#616161",
            command=lambda: self._close(False),
        ).pack(side="left")

    def _close(self, confirmo: bool):
        self.callback(confirmo)
        self.destroy()
