"""Modal de historial de comparaciones previas (QDialog).

Porta HistorialModal. Lista scrollable de comparaciones; click en una fila la restaura
(rellena el formulario) y cierra. Boton para limpiar todo el historial.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QWidget, QPushButton,
)
from PySide6.QtCore import Qt


def _fmt(v):
    try:
        return f"${int(round(float(v)))}"
    except (TypeError, ValueError):
        return str(v)


class _FilaHistorial(QFrame):
    """Fila clicable de una entrada del historial."""

    def __init__(self, entrada, on_click, parent=None):
        super().__init__(parent)
        self.setObjectName("chipRow")
        self._entrada = entrada
        self._on_click = on_click
        self.setCursor(Qt.PointingHandCursor)

        v = QVBoxLayout(self)
        v.setContentsMargins(12, 10, 12, 10)
        v.setSpacing(2)

        hotel = entrada.get("hotel", "")
        edificio = entrada.get("edificio") or ""
        nombre_hotel = f"{hotel} — {edificio}" if edificio else hotel
        t1 = QLabel(nombre_hotel); t1.setObjectName("cardTitle"); v.addWidget(t1)
        t2 = QLabel(entrada.get("habitacion", "")); t2.setObjectName("fieldLabel"); v.addWidget(t2)

        partes = []
        fe, fs = entrada.get("fecha_entrada", ""), entrada.get("fecha_salida", "")
        if fe or fs:
            partes.append(f"{fe} → {fs}")
        adultos, ninos = entrada.get("adultos", 1), entrada.get("ninos", 0)
        huesp = f"{adultos} adulto{'s' if adultos != 1 else ''}"
        if ninos:
            huesp += f", {ninos} niño{'s' if ninos != 1 else ''}"
        partes.append(huesp)
        ts = entrada.get("timestamp", "")
        if ts:
            partes.append(ts[:16].replace("T", " "))
        t3 = QLabel("   •   ".join(partes)); t3.setObjectName("mutedLabel"); v.addWidget(t3)

        for p in entrada.get("periodos", []):
            coincide = p.get("coincide", True)
            icono = "✓" if coincide else "⚠"
            nombre = p.get("nombre") or ""
            prefijo = f"{nombre}   " if nombre else ""
            texto = f"{prefijo}Excel: {_fmt(p.get('precio_excel',''))}   Web: {_fmt(p.get('precio_web',''))}   {icono}"
            lp = QLabel(texto)
            lp.setObjectName("mutedLabel" if coincide else "accentValue")
            v.addWidget(lp)

    def mousePressEvent(self, event):
        self._on_click(self._entrada)


class QtHistorialModal(QDialog):
    """Modal con la lista de comparaciones previas."""

    def __init__(self, parent, entradas, on_restaurar=None, on_limpiar=None):
        super().__init__(parent)
        self._on_restaurar = on_restaurar
        self._on_limpiar = on_limpiar

        self.setWindowTitle("Historial de comparaciones")
        self.resize(520, 480)
        self.setModal(True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(8)
        bl.setAlignment(Qt.AlignTop)

        if not entradas:
            vacio = QLabel("No hay comparaciones registradas.")
            vacio.setObjectName("mutedLabel")
            vacio.setAlignment(Qt.AlignCenter)
            bl.addWidget(vacio)
        else:
            for entrada in entradas:
                bl.addWidget(_FilaHistorial(entrada, self._click_fila))

        scroll.setWidget(body)
        lay.addWidget(scroll, stretch=1)

        if on_limpiar is not None and entradas:
            footer = QHBoxLayout()
            btn = QPushButton("Limpiar historial")
            btn.setObjectName("btnSecondary")
            btn.clicked.connect(self._click_limpiar)
            footer.addWidget(btn)
            footer.addStretch()
            lay.addLayout(footer)

    def _click_fila(self, entrada):
        if self._on_restaurar:
            self._on_restaurar(entrada)
        self.accept()

    def _click_limpiar(self):
        if self._on_limpiar:
            self._on_limpiar()
        self.accept()
