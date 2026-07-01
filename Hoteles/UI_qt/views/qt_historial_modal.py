"""Modal de historial de comparaciones previas (QDialog).

Porta HistorialModal. Lista scrollable de comparaciones; click en una fila la restaura
(rellena el formulario) y cierra. Boton para limpiar todo el historial.
Filas con html_resultado persitido muestran boton "Ver resultado" que abre
_ResultadoViewerDialog sin cerrar el historial.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QWidget,
    QPushButton, QTextBrowser,
)
from PySide6.QtCore import Qt

from UI_qt.widgets.qt_vista_resultados import QtVistaResultados


def _fmt(v):
    try:
        return f"${int(round(float(v)))}"
    except (TypeError, ValueError):
        return str(v)


class _FilaHistorial(QFrame):
    """Fila clicable de una entrada del historial."""

    def __init__(self, entrada, on_click, on_ver=None, parent=None):
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
        t1 = QLabel(nombre_hotel); t1.setObjectName("cardTitle"); t1.setWordWrap(True); v.addWidget(t1)
        t2 = QLabel(entrada.get("habitacion", "")); t2.setObjectName("fieldLabel"); t2.setWordWrap(True); v.addWidget(t2)

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

        periodos = entrada.get("periodos", [])
        has_result = on_ver and (
            entrada.get("html_resultado")
            or (entrada.get("periodos") and entrada.get("tiene_discrepancias"))
        )

        if has_result:
            row = QHBoxLayout()
            row.setContentsMargins(0, 4, 0, 0)
            row.setSpacing(8)
            prices_col = QVBoxLayout()
            prices_col.setSpacing(2)
            for p in periodos:
                coincide = p.get("coincide", True)
                icono = "✓" if coincide else "⚠"
                nombre = p.get("nombre") or ""
                prefijo = f"{nombre}   " if nombre else ""
                texto = f"{prefijo}Excel: {_fmt(p.get('precio_excel',''))}   Web: {_fmt(p.get('precio_web',''))}   {icono}"
                lp = QLabel(texto)
                lp.setObjectName("mutedLabel" if coincide else "accentValue")
                lp.setWordWrap(True)
                prices_col.addWidget(lp)
            row.addLayout(prices_col, stretch=1)
            btn = QPushButton("Ver resultado")
            btn.setObjectName("btnSecondary")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda: on_ver(self._entrada))
            row.addWidget(btn, alignment=Qt.AlignVCenter)
            v.addLayout(row)
        else:
            for p in periodos:
                coincide = p.get("coincide", True)
                icono = "✓" if coincide else "⚠"
                nombre = p.get("nombre") or ""
                prefijo = f"{nombre}   " if nombre else ""
                texto = f"{prefijo}Excel: {_fmt(p.get('precio_excel',''))}   Web: {_fmt(p.get('precio_web',''))}   {icono}"
                lp = QLabel(texto)
                lp.setObjectName("mutedLabel" if coincide else "accentValue")
                lp.setWordWrap(True)
                v.addWidget(lp)

    def mousePressEvent(self, event):
        self._on_click(self._entrada)


class _ResultadoViewerDialog(QDialog):
    """Muestra el resultado de una comparación previa, re-renderizado desde datos."""

    def __init__(self, entrada, on_email=None, parent=None, theme="light"):
        super().__init__(parent)
        hab = entrada.get("habitacion", "")
        ts = entrada.get("timestamp", "")[:16].replace("T", " ")
        self.setWindowTitle(f"{hab[:45]} — {ts}")
        self.resize(760, 520)
        self.setModal(True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        # Entradas viejas (sin fecha_inicio por periodo) caen al fallback de HTML guardado
        tiene_datos_nuevos = bool(
            entrada.get("periodos") and entrada["periodos"][0].get("fecha_inicio")
        )
        if tiene_datos_nuevos:
            vista = QtVistaResultados(theme=theme)
            vista.mostrar_resultado_desde_dict(entrada)
            lay.addWidget(vista, stretch=1)
        else:
            browser = QTextBrowser()
            browser.setOpenExternalLinks(True)
            browser.setHtml(entrada.get("html_resultado", "<i>Sin datos guardados.</i>"))
            lay.addWidget(browser, stretch=1)

        if on_email and entrada.get("tiene_discrepancias"):
            btn_mail = QPushButton("Enviar Email")
            btn_mail.setObjectName("btnPrimary")
            btn_mail.clicked.connect(lambda: on_email(entrada))
            lay.addWidget(btn_mail)


class QtHistorialModal(QDialog):
    """Modal con la lista de comparaciones previas."""

    def __init__(self, parent, entradas, on_restaurar=None, on_limpiar=None,
                 on_email=None, theme="light"):
        super().__init__(parent)
        self._on_restaurar = on_restaurar
        self._on_limpiar = on_limpiar
        self._on_email = on_email
        self._theme = theme

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
        bl.setContentsMargins(0, 0, 12, 0)
        bl.setSpacing(8)
        bl.setAlignment(Qt.AlignTop)

        if not entradas:
            vacio = QLabel("No hay comparaciones registradas.")
            vacio.setObjectName("mutedLabel")
            vacio.setAlignment(Qt.AlignCenter)
            bl.addWidget(vacio)
        else:
            for entrada in entradas:
                bl.addWidget(_FilaHistorial(entrada, self._click_fila, on_ver=self._click_ver))

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

    def _click_ver(self, entrada):
        dlg = _ResultadoViewerDialog(
            entrada, on_email=self._on_email, parent=self, theme=self._theme
        )
        dlg.exec()

    def _click_limpiar(self):
        if self._on_limpiar:
            self._on_limpiar()
        self.accept()
