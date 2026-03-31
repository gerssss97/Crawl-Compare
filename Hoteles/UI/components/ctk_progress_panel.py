"""Panel de progreso visual para la comparacion de precios."""

import customtkinter as ctk
from UI.styles import Colors, Typography, Spacing

# Pasos dentro de cada scraping (orden definido)
_STEPS = ["INIT", "FETCH", "SCRAPE", "EXTRACT", "COMPLETE"]
_STEP_LABELS = {
    "INIT": "Iniciando...",
    "FETCH": "Cargando pagina...",
    "SCRAPE": "Procesando HTML...",
    "EXTRACT": "Extrayendo con IA...",
    "COMPLETE": "Esperando resultados de la extracción...",
}


class CTkProgressPanel(ctk.CTkFrame):
    """Panel minimalista: label de estado + barra de progreso.

    La barra refleja el progreso real del scraping combinando
    periodos completados y el paso actual dentro del periodo en curso.

    Uso:
        panel = CTkProgressPanel(parent)
        panel.grid(...)
        panel.iniciar(total_periodos=3)
        panel.actualizar(periodo_actual=1, total=3, estado="Scrapeando...")
        panel.actualizar_step(step="FETCH")
        panel.finalizar(exito=True)
        panel.ocultar()
    """

    def __init__(self, master, grid_kwargs: dict | None = None, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("corner_radius", 0)
        kwargs.setdefault("border_width", 0)
        super().__init__(master, **kwargs)

        self._grid_kwargs = grid_kwargs or {}
        self._total_periodos = 1
        self._periodo_actual = 0
        self._construir()
        # No llamar grid() aquí: el componente empieza sin slot registrado

    def _construir(self):
        self.grid_columnconfigure(0, weight=1)

        self._lbl_estado = ctk.CTkLabel(
            self,
            text="",
            font=(Typography.FAMILY, Typography.SMALL),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        )
        self._lbl_estado.grid(row=0, column=0, sticky="ew", pady=(0, Spacing.XS))

        self._progress = ctk.CTkProgressBar(
            self,
            orientation="horizontal",
            height=10,
            corner_radius=5,
            fg_color=Colors.BORDER,
            progress_color=Colors.PRIMARY,
            mode="determinate",
        )
        self._progress.set(0)
        self._progress.grid(row=1, column=0, sticky="ew", pady=(0, Spacing.XS))

    # ------------------------------------------------------------------
    # Calculo de progreso combinado (periodos + step interno)
    # ------------------------------------------------------------------

    def _calcular_progreso(self, step: str) -> float:
        """Devuelve valor entre 0 y 1 combinando periodos completados + step actual."""
        if self._total_periodos <= 0:
            return 0.0
        step_idx = _STEPS.index(step) if step in _STEPS else 0
        # fraccion del periodo actual segun el step (0..1 dentro del periodo)
        step_fraction = step_idx / len(_STEPS)
        # periodos ya completados (el actual esta en progreso)
        periodos_completados = self._periodo_actual - 1
        valor = (periodos_completados + step_fraction) / self._total_periodos
        return max(0.0, min(1.0, valor))

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def mostrar(self):
        """Muestra el panel ocupando su slot en el grid."""
        self.grid(**self._grid_kwargs)

    def ocultar(self):
        """Oculta el panel y libera su espacio en el grid."""
        self.grid_forget()

    def iniciar(self, total_periodos: int):
        self._total_periodos = max(total_periodos, 1)
        self._periodo_actual = 0
        self._progress.set(0)
        self._progress.configure(progress_color=Colors.PRIMARY)
        self._lbl_estado.configure(text_color=Colors.TEXT_SECONDARY, text="Iniciando comparacion...")
        self.mostrar()

    def actualizar(self, periodo_actual: int, total: int, estado: str):
        self._periodo_actual = periodo_actual
        if total > 0:
            self._total_periodos = total
        self._lbl_estado.configure(text=estado)

    def actualizar_step(self, step: str):
        """Actualiza la barra con el paso actual del scraping dentro del periodo."""
        valor = self._calcular_progreso(step)
        self._progress.set(valor)
        label = _STEP_LABELS.get(step, step)
        if self._total_periodos > 1:
            texto = f"Periodo {self._periodo_actual}/{self._total_periodos}: {label}"
        else:
            texto = label
        self._lbl_estado.configure(text=texto)

    def marcar_periodo(self, indice: int, resultado: str):
        pass  # sin indicadores visuales por periodo

    def finalizar(self, exito: bool):
        self._progress.set(1)
        if exito:
            self._progress.configure(progress_color=Colors.SUCCESS)
            self._lbl_estado.configure(
                text="Comparacion completada - Todo coincide",
                text_color=Colors.SUCCESS,
            )
        else:
            self._progress.configure(progress_color=Colors.WARNING)
            self._lbl_estado.configure(
                text="Comparacion completada - Hay discrepancias",
                text_color=Colors.WARNING,
            )

    def mostrar_error(self, mensaje: str = "Error en la comparacion"):
        self._progress.configure(progress_color=Colors.ERROR)
        self._lbl_estado.configure(text=mensaje, text_color=Colors.ERROR)
