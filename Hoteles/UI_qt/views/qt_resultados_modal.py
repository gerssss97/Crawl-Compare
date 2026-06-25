"""Ventana de resultado de una comparacion (QWidget top-level, uno por comparison_id).

Porta ResultadosModal. Se conecta a los Signals del EventBridge (thread-safe) en vez
del EventBus directo, asi los handlers corren en el hilo de UI aunque el scraping
emita desde otro hilo. Filtra por comparison_id. Varios modales pueden coexistir
(comparaciones en paralelo). Header con resumen + progreso + vista de resultados +
boton email (si hay discrepancias).
"""

import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QMessageBox,
)
from PySide6.QtCore import Qt

from UI_qt.widgets.qt_progress_panel import QtProgressPanel
from UI_qt.widgets.qt_vista_resultados import QtVistaResultados


class QtResultadosModal(QWidget):
    """Modal independiente de progreso + resultado de una comparacion."""

    def __init__(self, parent, comparison_id, snapshot, bridge, historial_service,
                 controlador_comparacion=None, offset=0, theme="light"):
        super().__init__(None, Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._cid = comparison_id
        self._snap = snapshot
        self._bridge = bridge
        self._historial_service = historial_service
        self._ctrl_comparacion = controlador_comparacion
        self._theme = theme
        self._resultado = None
        self._btn_email = None

        hab = snapshot.get("habitacion", "")
        self.setWindowTitle(f"Comparando: {hab[:50]}...")
        self.setMinimumSize(600, 400)
        self.resize(780, 560)

        self._build_ui()
        self._connect_bridge()

        if parent is not None:
            self._reposicionar(parent, offset)

    # ---- UI ----
    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        lay.addWidget(self._build_header())

        self.progress = QtProgressPanel()
        self.progress.iniciar(total_periodos=1)
        lay.addWidget(self.progress)

        self.vista = QtVistaResultados(theme=self._theme)
        lay.addWidget(self.vista, stretch=1)

    def _build_header(self):
        s = self._snap
        hotel = s.get("hotel", "")
        edificio = s.get("edificio")
        hab = s.get("habitacion", "")
        f_ent = s.get("fecha_entrada", "")
        f_sal = s.get("fecha_salida", "")
        adultos = s.get("adultos", 1)
        ninos = s.get("ninos", 0)

        nombre_hotel = f"{hotel} — {edificio}" if edificio else hotel
        huesp = f"{adultos} adulto{'s' if adultos != 1 else ''}"
        if ninos:
            huesp += f", {ninos} niño{'s' if ninos != 1 else ''}"

        box = QFrame()
        box.setObjectName("card")
        v = QVBoxLayout(box)
        v.setContentsMargins(14, 10, 14, 10)
        v.setSpacing(2)
        t1 = QLabel(nombre_hotel); t1.setObjectName("cardTitle"); v.addWidget(t1)
        t2 = QLabel(hab); t2.setObjectName("mutedLabel"); v.addWidget(t2)
        t3 = QLabel(f"{f_ent} → {f_sal}   •   {huesp}"); t3.setObjectName("mutedLabel"); v.addWidget(t3)
        return box

    # ---- Bridge (signals thread-safe) ----
    def _connect_bridge(self):
        self._bridge.started.connect(self._on_started)
        self._bridge.progress.connect(self._on_progress)
        self._bridge.scrape_step.connect(self._on_scrape_step)
        self._bridge.completed.connect(self._on_completed)
        self._bridge.error.connect(self._on_error)

    def closeEvent(self, event):
        self._disconnect_bridge()
        event.accept()

    def _disconnect_bridge(self):
        for sig, slot in (
            (self._bridge.started, self._on_started),
            (self._bridge.progress, self._on_progress),
            (self._bridge.scrape_step, self._on_scrape_step),
            (self._bridge.completed, self._on_completed),
            (self._bridge.error, self._on_error),
        ):
            try:
                sig.disconnect(slot)
            except (RuntimeError, TypeError):
                pass

    def _mine(self, data):
        return isinstance(data, dict) and data.get("comparison_id") == self._cid

    # ---- Handlers (corren en hilo de UI gracias al bridge) ----
    def _on_started(self, data):
        if self._mine(data):
            self.progress.iniciar(total_periodos=1)

    def _on_progress(self, data):
        if not self._mine(data):
            return
        actual = data.get("periodo_actual", 1)
        total = data.get("total", 1)
        estado = data.get("estado", "")
        self.progress.actualizar(actual, total, estado)

    def _on_scrape_step(self, data):
        if self._mine(data):
            self.progress.actualizar_step(data.get("step", ""))

    def _on_completed(self, data):
        if not self._mine(data):
            return
        resultado = data.get("resultado")
        from Core.comparador_multiperiodo import ResultadoComparacionMultiperiodo
        if not isinstance(resultado, ResultadoComparacionMultiperiodo):
            return
        exito = not resultado.tiene_discrepancias
        self.progress.finalizar(exito=exito)
        self.vista.mostrar_resultado_multiperiodo(resultado)
        self._resultado = resultado
        self._guardar_historial(resultado)
        hab = self._snap.get("habitacion", "")[:40]
        self.setWindowTitle(f"{hab} — {'OK' if exito else 'Discrepancias'}")
        if resultado.tiene_discrepancias:
            self._mostrar_btn_email()

    def _on_error(self, data):
        if not self._mine(data):
            return
        self.progress.mostrar_error()
        self.vista.mostrar_error(data.get("error", "Error desconocido"))
        hab = self._snap.get("habitacion", "")[:40]
        self.setWindowTitle(f"{hab} — Error")

    # ---- Historial + email (reutiliza Core) ----
    def _guardar_historial(self, resultado):
        def _iso(d): return d.isoformat() if d else None
        try:
            hab_web = resultado.habitacion_web_matcheada
            self._historial_service.agregar({
                "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
                "hotel": self._snap.get("hotel", ""),
                "edificio": self._snap.get("edificio"),
                "habitacion": self._snap.get("habitacion", ""),
                "fecha_entrada": self._snap.get("fecha_entrada", ""),
                "fecha_salida": self._snap.get("fecha_salida", ""),
                "adultos": self._snap.get("adultos", 1),
                "ninos": self._snap.get("ninos", 0),
                "tiene_discrepancias": resultado.tiene_discrepancias,
                "habitacion_web": hab_web.nombre if hab_web else "",
                "habitacion_web_detalles": hab_web.detalles if hab_web else None,
                "mensaje_match": resultado.mensaje_match,
                "periodos": [
                    {
                        "nombre":           rp.periodo.nombre,
                        "fecha_inicio":     _iso(rp.periodo.fecha_inicio),
                        "fecha_fin":        _iso(rp.periodo.fecha_fin),
                        "precio_excel":     rp.precio_excel,
                        "precio_web":       rp.precio_web,
                        "coincide":         rp.coincide,
                        "diferencia":       rp.diferencia,
                        "fecha_inicio_real": _iso(rp.fecha_inicio_real),
                        "fecha_fin_real":    _iso(rp.fecha_fin_real),
                        "url_visitada":     rp.url_visitada,
                        "error_msg":        rp.error_msg,
                        "error_url":        rp.error_url,
                    }
                    for rp in resultado.periodos
                ],
            })
        except Exception as e:
            print(f"[historial] Error al guardar: {e}")

    def _mostrar_btn_email(self):
        if self._btn_email is not None:
            return
        self._btn_email = QPushButton("Enviar Email")
        self._btn_email.setObjectName("btnPrimary")
        self._btn_email.clicked.connect(self._abrir_email)
        self.layout().addWidget(self._btn_email)

    def _abrir_email(self):
        if not self._resultado or self._ctrl_comparacion is None:
            return
        mensaje = self._ctrl_comparacion.enviar_email(self._resultado, self._snap)
        if mensaje:
            QMessageBox.information(self, "Email", mensaje)

    def actualizar_tema(self, theme: str) -> None:
        """Actualiza el tema del modal cuando el usuario lo cambia en la ventana principal."""
        self._theme = theme
        self.vista.actualizar_tema(theme)

    def _reposicionar(self, parent, offset):
        try:
            geo = parent.frameGeometry()
            desp = offset * 28
            x = geo.x() + (geo.width() - self.width()) // 2 + desp
            y = geo.y() + (geo.height() - self.height()) // 2 + desp
            self.move(max(0, x), max(0, y))
        except Exception:
            pass
