"""Panel de periodos con filas expandibles (spec aprobada en Figma).

Reemplaza CTkPeriodosPanel. Cada periodo es una fila colapsable: chevron + nombre.
Al expandir, despliega el rango de fechas del periodo (definido en el Excel).
Agrupa por nombre de grupo como el panel CTk original.

API: actualizar_periodos(habitacion, hotel_excel) y limpiar().
"""

from collections import OrderedDict
from datetime import date

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QScrollArea, QWidget,
)
from PySide6.QtCore import Qt

from Models.habitacion_unificada import HabitacionUnificada
from Models.hotelExcel import HabitacionExcel


class _PeriodoRow(QFrame):
    """Fila simple de un periodo: muestra el rango de fechas directamente.

    Si el periodo tiene nombre propio, muestra 'Nombre: rango'; si no, solo el rango.
    Sin chevron ni despliegue (la etiqueta 'Período' generica no aportaba info).
    """

    def __init__(self, periodo, parent=None):
        super().__init__(parent)
        self.setObjectName("chipRow")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(0)

        ini = periodo.fecha_inicio.strftime("%d/%m/%Y")
        fin = periodo.fecha_fin.strftime("%d/%m/%Y")
        nombre = getattr(periodo, "nombre", None)
        texto = f"{nombre}: {ini} → {fin}" if nombre else f"{ini} → {fin}"

        lbl = QLabel(texto)
        lbl.setObjectName("sectionLabel")
        lay.addWidget(lbl)


class QtPeriodosPanel(QFrame):
    """Panel de periodos de la habitacion (filas expandibles agrupadas)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(10)

        title = QLabel("PERÍODOS DEFINIDOS")
        title.setObjectName("sectionLabel")
        outer.addWidget(title)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(self._scroll, stretch=1)

        self._body = QWidget()
        self._body_lay = QVBoxLayout(self._body)
        self._body_lay.setContentsMargins(0, 0, 0, 0)
        self._body_lay.setSpacing(8)
        self._body_lay.setAlignment(Qt.AlignTop)
        self._scroll.setWidget(self._body)

        self._mostrar_mensaje("(ninguna seleccionada)")

    def _mostrar_mensaje(self, mensaje):
        self._clear()
        lbl = QLabel(mensaje)
        lbl.setObjectName("mutedLabel")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        self._body_lay.addWidget(lbl)

    def limpiar(self):
        self._mostrar_mensaje("(ninguna seleccionada)")

    def actualizar_periodos(self, habitacion, hotel_excel, ocultar_vencidos: bool = False):
        self._clear()

        if isinstance(habitacion, HabitacionUnificada):
            periodo_ids = habitacion.todos_los_periodos()
        elif isinstance(habitacion, HabitacionExcel):
            periodo_ids = habitacion.periodo_ids
        else:
            periodo_ids = getattr(habitacion, "periodo_ids", set())

        if not periodo_ids:
            self._mostrar_mensaje("Sin períodos asignados")
            return

        # Agrupar por nombre de grupo (como el panel CTk)
        hoy = date.today()
        tuvo_periodos = False
        grupos = OrderedDict()
        for pid in periodo_ids:
            periodo = hotel_excel.periodo_por_id(pid)
            if not periodo:
                continue
            tuvo_periodos = True
            if ocultar_vencidos and periodo.fecha_fin < hoy:
                continue
            nombre_grupo = None
            for grupo in hotel_excel.periodos_group:
                if periodo in grupo.periodos:
                    nombre_grupo = grupo.nombre
                    break
            if nombre_grupo:
                grupos.setdefault(nombre_grupo, []).append(periodo)

        if not grupos:
            msg = ("Todos los períodos están vencidos." if (ocultar_vencidos and tuvo_periodos)
                   else "Sin períodos asignados")
            self._mostrar_mensaje(msg)
            return

        for nombre_grupo, periodos in grupos.items():
            cab = QLabel(nombre_grupo)
            cab.setObjectName("fieldLabel")
            self._body_lay.addWidget(cab)
            for periodo in periodos:
                self._body_lay.addWidget(_PeriodoRow(periodo))

    def _clear(self):
        while self._body_lay.count():
            it = self._body_lay.takeAt(0)
            w = it.widget()
            if w is not None:
                w.deleteLater()
