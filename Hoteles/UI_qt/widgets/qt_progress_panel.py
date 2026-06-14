"""Panel de progreso del scraping: label de estado + QProgressBar.

Porta CTkProgressPanel. La barra combina periodos completados + step actual dentro
del periodo en curso (mismo calculo). QProgressBar usa rango 0..1000 (entero) para
representar la fraccion 0..1 con resolucion suficiente.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar

_STEPS = ["INIT", "FETCH", "SCRAPE", "EXTRACT", "COMPLETE"]
_STEP_LABELS = {
    "INIT": "Iniciando...",
    "FETCH": "Cargando pagina...",
    "SCRAPE": "Procesando HTML...",
    "EXTRACT": "Extrayendo con IA...",
    "COMPLETE": "Esperando resultados de la extracción...",
}
_SCALE = 1000


class QtProgressPanel(QWidget):
    """Label de estado + barra de progreso del scraping."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._total = 1
        self._actual = 0

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        self._lbl = QLabel("")
        self._lbl.setObjectName("mutedLabel")
        lay.addWidget(self._lbl)

        self._bar = QProgressBar()
        self._bar.setRange(0, _SCALE)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(10)
        lay.addWidget(self._bar)

    def _frac(self, step):
        if self._total <= 0:
            return 0.0
        idx = _STEPS.index(step) if step in _STEPS else 0
        step_fraction = idx / len(_STEPS)
        completados = self._actual - 1
        val = (completados + step_fraction) / self._total
        return max(0.0, min(1.0, val))

    def iniciar(self, total_periodos):
        self._total = max(total_periodos, 1)
        self._actual = 0
        self._bar.setValue(0)
        self._set_bar_color("#2563EB")
        self._lbl.setText("Iniciando comparación...")
        self.setVisible(True)

    def actualizar(self, periodo_actual, total, estado):
        self._actual = periodo_actual
        if total > 0:
            self._total = total
        self._lbl.setText(estado)

    def actualizar_step(self, step):
        self._bar.setValue(int(self._frac(step) * _SCALE))
        label = _STEP_LABELS.get(step, step)
        if self._total > 1:
            self._lbl.setText(f"Periodo {self._actual}/{self._total}: {label}")
        else:
            self._lbl.setText(label)

    def finalizar(self, exito):
        self._bar.setValue(_SCALE)
        if exito:
            self._set_bar_color("#10B981")
            self._lbl.setText("Comparación completada — Todo coincide")
        else:
            self._set_bar_color("#F59E0B")
            self._lbl.setText("Comparación completada — Hay discrepancias")

    def mostrar_error(self, mensaje="Error en la comparación"):
        self._set_bar_color("#EF4444")
        self._lbl.setText(mensaje)

    def ocultar(self):
        self.setVisible(False)

    def _set_bar_color(self, color):
        self._bar.setStyleSheet(
            f"QProgressBar {{ background:#E2E8F0; border:none; border-radius:5px; }}"
            f"QProgressBar::chunk {{ background:{color}; border-radius:5px; }}"
        )
