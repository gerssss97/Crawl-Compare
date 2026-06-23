"""Ventana principal PySide6 (Fase 2: shell + estilo).

QMainWindow con header + layout 2 columnas (65/35), QSS dual-mode generado desde
las constantes del proyecto, y toggle de tema en vivo. Los paneles internos son
placeholders por ahora: se reemplazan por componentes reales en las Fases 3-4.
Cableada al AppState v2 (UI_qt/state) de la Fase 1.
"""

import sys
import os
import datetime

# UTF-8 en stdout/stderr: el Core hace print() con caracteres Unicode (ej. "→") y la
# consola de Windows usa cp1252 por default -> UnicodeEncodeError que el scraping
# capturaba como "ERROR en periodo". Reconfigurar a UTF-8 lo resuelve sin tocar el Core
# (replica lo que hace el logger del .exe). Debe ir antes de cualquier import que imprima.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass  # stream sin reconfigure (ej. redirigido) -> se ignora

# Bootstrap de path: permite ejecutar este archivo directamente (python interfaz_qt.py)
# ademas de importarlo como modulo. Debe ir ANTES de importar UI_qt.*
if __package__ in (None, ""):
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, _base)
    sys.path.insert(0, os.path.join(_base, "Hoteles"))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame,
    QLabel, QPushButton, QGraphicsDropShadowEffect, QSizePolicy,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor

from UI_qt.styles import qt_icons

from UI_qt.state import EventBus, AppState
from UI_qt.state.event_bridge import EventBridge
from UI_qt.styles import PALETTES, build_qss
from UI_qt.widgets import QtFormReserva, QtFormFechas, QtPrecioPanel, QtPeriodosPanel
from UI_qt.views import QtResultadosModal, QtHistorialModal, QtConfigModal

from Core.services import ConfigService
from Core.controller import GestorService
from UI.controllers import (
    ControladorHotel, ControladorPrecios, ControladorValidacion, ControladorComparacion,
)
from UI.services.historial_service import HistorialService
from UI.utils import normalizar_hotel_nombre


def card_shadow(palette):
    """Crea el efecto de sombra de card (QSS no tiene box-shadow)."""
    eff = QGraphicsDropShadowEffect()
    r, g, b, a = palette.shadow_rgba
    eff.setColor(QColor(r, g, b, a))
    eff.setBlurRadius(palette.shadow_blur)
    eff.setOffset(0, 2)
    return eff


class MainWindow(QMainWindow):
    """Ventana principal de la app (shell de la migracion PySide6)."""

    def __init__(self, theme: str = "light"):
        super().__init__()
        self._theme = theme
        self.event_bus = EventBus()
        self.state = AppState(self.event_bus)

        # Controladores reutilizados de UI/ (sin cambios)
        self.controlador_validacion = ControladorValidacion(self.state)
        self.controlador_hotel = ControladorHotel(self.state, self.event_bus)
        self.controlador_precios = ControladorPrecios(self.state, self.event_bus)
        self.controlador_comparacion = ControladorComparacion(
            self.state, self.event_bus, self.controlador_validacion,
        )
        self.config_service = ConfigService()
        self.historial_service = HistorialService(self.config_service)

        # Puente EventBus -> Qt Signals (thread-safe para el scraping en otro hilo)
        self.bridge = EventBridge(self.event_bus)
        self._modales = {}          # comparison_id -> QtResultadosModal
        self._ctx_pendiente = None  # contexto del intento en curso (para gap modal)

        # Carga inicial del Excel (si hay uno configurado)
        self._excel_path = self.controlador_hotel.cargar_excel_inicial(self.config_service)
        if self._excel_path:
            self.config_service.set_last_excel_path(self._excel_path)

        self.setWindowTitle("Comparador de Precios de Hoteles")
        self.resize(1280, 800)
        self.setMinimumSize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_body(), stretch=1)

        self._apply_theme(theme)

        # Todos los eventos pasan por el bridge (thread-safe)
        self.bridge.precios_actualizados.connect(self._on_precios_actualizados)
        self.bridge.habitacion_unificada_changed.connect(self._on_habitacion_para_periodos)
        self.bridge.started.connect(self._on_comparison_started)
        self.bridge.validation_failed.connect(self._on_validation_failed)
        self.bridge.mostrar_modal_gaps.connect(self._on_mostrar_modal_gaps)

        # Poblar hoteles una vez armada la UI
        if self.controlador_hotel.esta_cargado():
            self.form_reserva.cargar_hoteles()

    # ===================== Handlers paneles de resultado =====================
    def _on_precios_actualizados(self, data):
        """Actualiza el panel de precio segun el evento de ControladorPrecios."""
        tipo = data.get("tipo")
        gap = data.get("gap_analysis")
        if tipo in ("sin_fechas", "sin_periodos"):
            self.precio_panel.mostrar_mensaje(data.get("mensaje", ""))
        elif tipo == "precios_calculados":
            self.precio_panel.mostrar_precios_multiples(data["precios"], gap)

    def _on_habitacion_para_periodos(self, data):
        """Actualiza el panel de periodos con la habitacion elegida."""
        habitacion = data.get("value") if isinstance(data, dict) else data
        hotel_nombre = normalizar_hotel_nombre(self.state.hotel.get())
        hotel_actual = next(
            (h for h in self.state.hoteles_excel if h.nombre.lower() == hotel_nombre), None
        )
        if hotel_actual is None:
            self.periodos_panel.limpiar()
            return
        self.periodos_panel.actualizar_periodos(habitacion, hotel_actual)

    # ===================== Ejecucion de la comparacion =====================
    def _ejecutar_comparacion(self):
        """Genera comparison_id, guarda el snapshot y lanza la comparacion async."""
        cid = datetime.datetime.now().isoformat(timespec="microseconds")
        snapshot = {
            "hotel": self.state.hotel.get(),
            "edificio": self.state.edificio.get() or None,
            "habitacion": self.state.habitacion.get(),
            "fecha_entrada": self.state.fecha_entrada_completa.get(),
            "fecha_salida": self.state.fecha_salida_completa.get(),
            "adultos": self.state.adultos.get(),
            "ninos": self.state.ninos.get(),
            "periodos_precio": list(self.state.periodos_precio),
        }
        self._ctx_pendiente = {"id": cid, "snapshot": snapshot}
        self.controlador_comparacion.ejecutar_comparacion_async(cid)

    def _on_comparison_started(self, data):
        """Abre el modal de resultados cuando arranca la comparacion."""
        ctx = self._ctx_pendiente
        if not ctx or data.get("comparison_id") != ctx.get("id"):
            return
        self._lanzar_modal(ctx["id"], ctx["snapshot"])
        self._ctx_pendiente = None

    def _lanzar_modal(self, comparison_id, snapshot):
        modal = QtResultadosModal(
            parent=self, comparison_id=comparison_id, snapshot=snapshot,
            bridge=self.bridge, historial_service=self.historial_service,
            controlador_comparacion=self.controlador_comparacion,
            offset=len(self._modales), theme=self._theme,
        )
        self._modales[comparison_id] = modal
        modal.destroyed.connect(lambda *_: self._modales.pop(comparison_id, None))
        modal.show()

    def _on_validation_failed(self, data):
        """Muestra los errores de validacion en un messagebox."""
        from PySide6.QtWidgets import QMessageBox
        mensajes = data.get("mensajes", "") if isinstance(data, dict) else str(data)
        QMessageBox.warning(self, "Datos incompletos o inválidos",
                            "Revisá los siguientes campos:\n\n" + mensajes)

    def _on_mostrar_modal_gaps(self, data):
        """Confirmacion antes de comparar con cobertura parcial (gaps)."""
        from PySide6.QtWidgets import QMessageBox
        gap_analysis = data.get("gap_analysis")
        ctx = self._ctx_pendiente
        try:
            desc = gap_analysis.get_gap_description()
        except Exception:
            desc = "Hay fechas sin precio en el Excel."
        resp = QMessageBox.question(
            self, "Cobertura parcial",
            f"{desc}\n\n¿Querés continuar igual con la comparación?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if resp == QMessageBox.Yes and ctx:
            self.controlador_comparacion.confirmar_gap()
            self._lanzar_modal(ctx["id"], ctx["snapshot"])
            self.controlador_comparacion.ejecutar_comparacion_async(ctx["id"])
        else:
            self.controlador_comparacion.resetear_gap()
            self._ctx_pendiente = None


    # ===================== Header: acciones =====================
    def _cambiar_excel(self):
        """File picker para cambiar el Excel; recarga y refresca la UI."""
        from pathlib import Path
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        current = self.controlador_hotel.get_excel_path()
        initialdir = str(Path(current).parent) if current else str(Path.home())
        self.activateWindow()
        self.raise_()
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo Excel", initialdir,
            "Archivos Excel (*.xlsx);;Todos los archivos (*.*)",
        )
        if not path:
            return
        try:
            self.controlador_hotel.cargar_excel(path)
        except Exception as e:
            QMessageBox.critical(self, "Error al cargar Excel",
                                 f"No se pudo cargar el archivo:\n{path}\n\nDetalle: {e}")
            return
        self._excel_path = path
        self.config_service.set_last_excel_path(path)
        self._actualizar_label_excel(path)
        self.btn_ejecutar.setEnabled(True)
        self.form_reserva.cargar_hoteles()

    def _actualizar_label_excel(self, path):
        from pathlib import Path
        if path is None:
            self.lbl_excel.setText("Sin Excel cargado")
        else:
            nombre = Path(path).name
            display = nombre if len(nombre) <= 30 else nombre[:27] + "..."
            self.lbl_excel.setText(display)

    def _abrir_historial(self):
        """Abre el modal de historial con las comparaciones previas."""
        entradas = self.historial_service.obtener_todos()
        modal = QtHistorialModal(
            self, entradas,
            on_restaurar=self._on_historial_restaurar,
            on_limpiar=self.historial_service.limpiar_todo,
            on_ver=self._on_historial_ver,
            on_email=self._on_historial_email,
        )
        modal.exec()

    def _on_historial_ver(self, entrada):
        """Abre el viewer con el HTML persistido de la comparación."""
        from UI_qt.views.qt_historial_modal import _ResultadoViewerDialog
        dlg = _ResultadoViewerDialog(entrada, on_email=self._on_historial_email, parent=self)
        dlg.exec()

    def _on_historial_email(self, entrada):
        """Construye y despacha un email desde los datos del historial."""
        from Core.services.email_senders import ClipboardSender, get_sender
        from PySide6.QtWidgets import QMessageBox

        hotel = entrada.get("hotel", "")
        habitacion = entrada.get("habitacion", "")
        hab_web = entrada.get("habitacion_web", "")
        periodos = entrada.get("periodos", [])
        firma = self.config_service.get_email_firma()

        lineas = [
            "Estimado equipo de reservas,", "",
            f"He detectado discrepancias de precios en el hotel {hotel}.", "",
            f"Habitación Excel: {habitacion}",
        ]
        if hab_web:
            lineas.append(f"Habitación Web: {hab_web}")
        lineas += ["", "PERIODOS CON DISCREPANCIA:"]

        for i, p in enumerate(periodos, 1):
            if p.get("coincide", True):
                continue
            nombre = p.get("nombre") or f"Periodo {i}"
            excel, web = p.get("precio_excel", ""), p.get("precio_web", "")
            try:
                excel_str = f"${float(excel):.2f}"
                web_str = f"${float(web):.2f}"
                diff_str = f"${abs(float(excel) - float(web)):.2f}"
            except (TypeError, ValueError):
                excel_str = web_str = diff_str = "N/A"
            lineas += [
                "", f"{nombre}:",
                f"  Excel: {excel_str}   Web: {web_str}   Diferencia: {diff_str}",
            ]

        lineas += ["", "Saludos cordiales,", firma]
        cuerpo = "\n".join(lineas)

        sender = get_sender(self.config_service.get_email_provider())
        sender.enviar("", f"Reporte de Discrepancias - {hotel}", cuerpo)
        if isinstance(sender, ClipboardSender):
            msg = ("Email copiado al portapapeles.\nAbrí tu cliente de email y pegá con Ctrl+V."
                   if sender.copied else "No se pudo copiar al portapapeles (pyperclip no disponible).")
            QMessageBox.information(self, "Email", msg)

    def _on_historial_restaurar(self, entrada):
        """Pre-rellena el formulario con una entrada del historial."""
        hotel = entrada.get("hotel", "")
        edificio = entrada.get("edificio") or ""
        habitacion = entrada.get("habitacion", "")

        # Hotel primero: dispara la carga de edificios/habitaciones
        self.state.hotel.set(hotel)
        self.form_reserva._on_hotel_changed(hotel)

        # Fechas: DD-MM-AAAA -> setear en los QDateField
        from PySide6.QtCore import QDate

        def _set_fecha(field, completa):
            partes = completa.split("-") if completa else []
            if len(partes) == 3:
                d, m, a = int(partes[0]), int(partes[1]), int(partes[2])
                field.edit.setDate(QDate(a, m, d))

        _set_fecha(self.form_fechas.fecha_entrada, entrada.get("fecha_entrada", ""))
        _set_fecha(self.form_fechas.fecha_salida, entrada.get("fecha_salida", ""))
        self.state.adultos.set(entrada.get("adultos", 1))
        self.state.ninos.set(entrada.get("ninos", 0))

        # Edificio/habitacion: el combo necesita estar poblado; se setean tras el render
        from PySide6.QtCore import QTimer

        def _set_edif_hab():
            if edificio:
                self.state.edificio.set(edificio)
                self.form_reserva._on_edificio_changed(edificio)
                QTimer.singleShot(150, lambda: self.state.habitacion.set(habitacion))
            else:
                self.state.habitacion.set(habitacion)
        QTimer.singleShot(100, _set_edif_hab)

    def _abrir_config(self):
        """Abre el modal de configuracion."""
        QtConfigModal(self, excel_path=self.controlador_hotel.get_excel_path()).exec()

    # ===================== Header =====================
    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(60)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(24, 0, 24, 0)
        lay.setSpacing(16)

        title = QLabel("Comparador de Precios de Hoteles")
        title.setObjectName("headerTitle")
        lay.addWidget(title)

        btn_hist = QPushButton("  Historial")
        btn_hist.setObjectName("headerChip")
        btn_hist.setIcon(qt_icons.icon("clock", on_dark=True))
        btn_hist.setIconSize(QSize(16, 16))
        btn_hist.clicked.connect(self._abrir_historial)
        lay.addWidget(btn_hist)

        lay.addStretch()

        self.lbl_excel = QLabel("Extracto.xlsx")
        self.lbl_excel.setObjectName("headerExcel")
        lay.addWidget(self.lbl_excel)

        btn_cambiar = QPushButton("Cambiar")
        btn_cambiar.setObjectName("headerChip")
        btn_cambiar.clicked.connect(self._cambiar_excel)
        lay.addWidget(btn_cambiar)

        # Toggle de tema (para probar dual mode en vivo)
        self.btn_theme = QPushButton("🌙" if self._theme == "light" else "☀")
        self.btn_theme.setObjectName("headerGear")
        self.btn_theme.setFixedSize(34, 34)
        self.btn_theme.clicked.connect(self._toggle_theme)
        lay.addWidget(self.btn_theme)

        btn_gear = QPushButton()
        btn_gear.setObjectName("headerGear")
        btn_gear.setIcon(qt_icons.icon("settings", on_dark=True))
        btn_gear.setIconSize(QSize(18, 18))
        btn_gear.setFixedSize(34, 34)
        btn_gear.clicked.connect(self._abrir_config)
        lay.addWidget(btn_gear)

        return header

    # ===================== Body 2 columnas =====================
    def _build_body(self) -> QWidget:
        body = QWidget()
        lay = QHBoxLayout(body)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(24)
        lay.addWidget(self._build_left(), stretch=65)
        lay.addWidget(self._build_right(), stretch=35)
        return body

    def _make_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setGraphicsEffect(card_shadow(PALETTES[self._theme]))
        return card

    def _build_left(self) -> QWidget:
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(16)

        # Card 1: seleccion de reserva (form real)
        self.form_reserva = QtFormReserva(
            self.state, self.controlador_hotel, self.event_bus,
            on_limpiar=self._limpiar_campos,
        )
        self.form_reserva.setGraphicsEffect(card_shadow(PALETTES[self._theme]))
        v.addWidget(self.form_reserva)

        # Card 2: fechas y huespedes (form real). El color de resaltado del dia
        # seleccionado en el calendario sale del acento del tema actual.
        self.form_fechas = QtFormFechas(self.state, highlight_color=PALETTES[self._theme].accent)
        self.form_fechas.setGraphicsEffect(card_shadow(PALETTES[self._theme]))
        v.addWidget(self.form_fechas)

        self.btn_ejecutar = QPushButton("Ejecutar Comparación")
        self.btn_ejecutar.setObjectName("btnPrimary")
        self.btn_ejecutar.clicked.connect(self._ejecutar_comparacion)
        v.addWidget(self.btn_ejecutar)
        v.addStretch()
        return wrap

    def _limpiar_campos(self):
        """Resetea el formulario (replica _limpiar_campos de interfaz_ctk)."""
        self.state.reset_all()
        self.form_reserva._ocultar_edificio()
        self.form_fechas.clear()
        self.precio_panel.limpiar()
        self.periodos_panel.limpiar()
        if GestorService.esta_cargado():
            self.form_reserva.cargar_hoteles()

    def _build_right(self) -> QWidget:
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(16)

        self.precio_panel = QtPrecioPanel(self.state)
        self.precio_panel.setGraphicsEffect(card_shadow(PALETTES[self._theme]))
        v.addWidget(self.precio_panel, stretch=1)

        self.periodos_panel = QtPeriodosPanel()
        self.periodos_panel.setGraphicsEffect(card_shadow(PALETTES[self._theme]))
        v.addWidget(self.periodos_panel, stretch=1)
        return wrap

    # ===================== Tema =====================
    def _apply_theme(self, theme: str):
        self._theme = theme
        QApplication.instance().setStyleSheet(build_qss(theme))
        for card in self.findChildren(QFrame, "card"):
            card.setGraphicsEffect(card_shadow(PALETTES[theme]))
        # Propagar tema a modales de comparacion ya abiertos
        for modal in list(self._modales.values()):
            try:
                modal.actualizar_tema(theme)
            except Exception:
                pass

    def _toggle_theme(self):
        nuevo = "dark" if self._theme == "light" else "light"
        self._apply_theme(nuevo)
        self.btn_theme.setText("🌙" if nuevo == "light" else "☀")

    def closeEvent(self, event):
        """Al cerrar la ventana, desconecta el bridge antes de destruir los widgets.

        Sin esto, si hay scraping corriendo al cerrar, el bridge puede emitir signals
        a slots de widgets ya destruidos -> RuntimeError: Internal C++ object deleted.
        """
        self.bridge.blockSignals(True)
        for modal in list(self._modales.values()):
            try:
                modal.close()
            except Exception:
                pass
        self._modales.clear()
        super().closeEvent(event)


def run():
    """Punto de entrada de la UI PySide6."""
    app = QApplication(sys.argv)
    win = MainWindow(theme="light")
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    # El path ya quedo seteado en el bootstrap del tope del archivo.
    os.chdir(os.path.join(_base, "Hoteles"))
    run()
