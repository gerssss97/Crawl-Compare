"""Card 'Fechas y Huespedes': fecha entrada/salida (con validacion cruzada) + adultos/ninos.

La validacion entrada<salida es PREVENTIVA: al cambiar la entrada, se fija el minimo
del QDateEdit de salida en entrada+1 dia, asi el widget no permite elegir una salida
invalida. El ControladorValidacion (reutilizado) queda como red de seguridad final.
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QWidget,
)
from PySide6.QtCore import QDate, QSize
from UI_qt.widgets.qt_date_edit import QtDateField
from UI_qt.styles import qt_icons


class QtFormFechas(QFrame):
    """Card de fechas y huespedes."""

    def __init__(self, state, highlight_color="#2563EB", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.state = state

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        head = QHBoxLayout()
        head.setSpacing(8)
        icono = QLabel()
        icono.setPixmap(qt_icons.icon("clock").pixmap(QSize(18, 18)))
        head.addWidget(icono)
        title = QLabel("FECHAS Y HUÉSPEDES")
        title.setObjectName("cardTitle")
        head.addWidget(title)
        head.addStretch()
        lay.addLayout(head)

        row = QHBoxLayout()
        row.setSpacing(12)

        self.fecha_entrada = QtDateField(
            "Fecha de entrada",
            state.fecha_dia_entrada, state.fecha_mes_entrada, state.fecha_ano_entrada,
            default_offset_days=0,   # hoy
            on_change=self._on_entrada_changed,
            highlight_color=highlight_color,
        )
        row.addWidget(self.fecha_entrada, stretch=1)

        self.fecha_salida = QtDateField(
            "Fecha de salida",
            state.fecha_dia_salida, state.fecha_mes_salida, state.fecha_ano_salida,
            default_offset_days=1,   # mañana
            highlight_color=highlight_color,
        )
        row.addWidget(self.fecha_salida, stretch=1)

        # Consolidar dia/mes/anio -> fecha_*_completa (DD-MM-AAAA), como en interfaz_ctk.
        # ControladorPrecios escucha fecha_*_completa, asi que esto dispara el calculo.
        for var in (state.fecha_dia_entrada, state.fecha_mes_entrada, state.fecha_ano_entrada):
            var.trace_add('write', self._actualizar_entrada_completa)
        for var in (state.fecha_dia_salida, state.fecha_mes_salida, state.fecha_ano_salida):
            var.trace_add('write', self._actualizar_salida_completa)

        # Validacion preventiva inicial + sembrar fecha_*_completa
        self._on_entrada_changed()
        self._actualizar_entrada_completa()
        self._actualizar_salida_completa()

        row.addWidget(self._huesped("Adultos", state.adultos, 1))
        row.addWidget(self._huesped("Niños", state.ninos, 0))

        lay.addLayout(row)

    def _huesped(self, label, variable, default):
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        lbl = QLabel(label)
        lbl.setObjectName("fieldLabel")
        v.addWidget(lbl)
        spin = QSpinBox()
        spin.setRange(0, 20)
        spin.setValue(default)
        spin.setFixedWidth(80)
        spin.valueChanged.connect(lambda val: variable.set(val))
        v.addWidget(spin)
        return wrap

    def _on_entrada_changed(self):
        """Validacion preventiva: la salida no puede ser <= entrada."""
        entrada = self.fecha_entrada.date()
        self.fecha_salida.set_minimum(entrada.addDays(1))

    def _actualizar_entrada_completa(self, *_args):
        """Consolida dia/mes/anio de entrada en fecha_entrada_completa (DD-MM-AAAA)."""
        d = self.state.fecha_dia_entrada.get()
        m = self.state.fecha_mes_entrada.get()
        a = self.state.fecha_ano_entrada.get()
        self.state.fecha_entrada_completa.set(f"{d}-{m}-{a}" if (d and m and a) else "")

    def _actualizar_salida_completa(self, *_args):
        """Consolida dia/mes/anio de salida en fecha_salida_completa (DD-MM-AAAA)."""
        d = self.state.fecha_dia_salida.get()
        m = self.state.fecha_mes_salida.get()
        a = self.state.fecha_ano_salida.get()
        self.state.fecha_salida_completa.set(f"{d}-{m}-{a}" if (d and m and a) else "")

    def clear(self):
        self.fecha_entrada.clear()
        self.fecha_salida.clear()
