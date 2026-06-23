"""Card 'Seleccion de Reserva': hotel + edificio (dinamico) + habitacion.

Replica la logica de _crear_form_reserva / _on_hotel_changed / _mostrar_edificio
de interfaz_ctk.py, pero con QComboBox y atado al AppState v2. Usa ControladorHotel
(reutilizado de UI/) para poblar edificios y habitaciones.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import QSize
from UI_qt.widgets.qt_labeled_combo import QtLabeledCombo
from UI_qt.styles import qt_icons
from UI.utils import normalizar_hotel_nombre


class QtFormReserva(QFrame):
    """Card de seleccion de reserva (hotel/edificio/habitacion)."""

    def __init__(self, state, controlador_hotel, event_bus, on_limpiar=None, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.state = state
        self.ctrl = controlador_hotel
        self.event_bus = event_bus
        self._on_limpiar = on_limpiar
        self._edificio_visible = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        # Header de la card: icono + titulo + boton Limpiar
        head = QHBoxLayout()
        head.setSpacing(8)
        icono = QLabel()
        icono.setPixmap(qt_icons.icon("home").pixmap(QSize(18, 18)))
        head.addWidget(icono)
        title = QLabel("SELECCIÓN DE RESERVA")
        title.setObjectName("cardTitle")
        head.addWidget(title)
        head.addStretch()
        btn_limpiar = QPushButton("  Limpiar")
        btn_limpiar.setObjectName("btnSecondary")
        btn_limpiar.setIcon(qt_icons.icon("trash"))
        btn_limpiar.setIconSize(QSize(14, 14))
        btn_limpiar.clicked.connect(self._limpiar)
        head.addWidget(btn_limpiar)
        lay.addLayout(head)

        # Fila hotel + edificio
        self._row = QHBoxLayout()
        self._row.setSpacing(12)
        self.combo_hotel = QtLabeledCombo("Hotel", state.hotel, on_change=self._on_hotel_changed)
        self._row.addWidget(self.combo_hotel, stretch=1)
        self.combo_edificio = QtLabeledCombo("Edificio", state.edificio, on_change=self._on_edificio_changed)
        self.combo_edificio.setVisible(False)   # oculto hasta que el hotel tenga tipos
        self._row.addWidget(self.combo_edificio, stretch=1)
        lay.addLayout(self._row)

        # Habitacion
        self.combo_habitacion = QtLabeledCombo("Habitación", state.habitacion,
                                               on_change=self._on_habitacion_changed)
        lay.addWidget(self.combo_habitacion)

    # ---- poblar ----
    def cargar_hoteles(self):
        nombres = self.ctrl.cargar_hoteles()
        self.combo_hotel.set_values(nombres)

    # ---- handlers ----
    def _normalizar(self, nombre):
        n = nombre.replace(" (a)", "").replace(" (A)", "").strip()
        return " ".join(w.capitalize() for w in n.split())

    def _on_hotel_changed(self, hotel):
        if not hotel:
            return
        hotel_lower = normalizar_hotel_nombre(hotel)
        for he in self.state.hoteles_excel:
            if he.nombre.lower() == hotel_lower:
                if he.tipos:
                    self._mostrar_edificio()
                    edificios = self.ctrl.cargar_edificios(self._normalizar(hotel))
                    self.combo_edificio.set_values(edificios)
                    self.state.edificio.set("")
                    self.combo_habitacion.set_values([])
                    self.state.habitacion.set("")
                else:
                    self._ocultar_edificio()
                    habs = self.ctrl.cargar_habitaciones(self._normalizar(hotel))
                    self.combo_habitacion.set_values(habs)
                    self.state.habitacion.set("")
                self.event_bus.emit("habitacion_unificada_changed", None)
                return

    def _on_edificio_changed(self, edificio):
        hotel = self.state.hotel.get()
        habs = self.ctrl.cargar_habitaciones(self._normalizar(hotel), edificio)
        self.combo_habitacion.set_values(habs)
        self.state.habitacion.set("")

    def _on_habitacion_changed(self, nombre):
        if not nombre or not self.state.habitaciones_unificadas:
            return
        hab = next((h for h in self.state.habitaciones_unificadas if h.nombre == nombre), None)
        if hab is None:
            return
        # Mismo evento que la UI CTk -> ControladorPrecios reacciona igual
        self.event_bus.emit("habitacion_unificada_changed", hab)

    # ---- visibilidad edificio ----
    def _mostrar_edificio(self):
        if not self._edificio_visible:
            self.combo_edificio.setVisible(True)
            self._edificio_visible = True

    def _ocultar_edificio(self):
        if self._edificio_visible:
            self.combo_edificio.setVisible(False)
            self._edificio_visible = False

    def _limpiar(self):
        if self._on_limpiar:
            self._on_limpiar()
