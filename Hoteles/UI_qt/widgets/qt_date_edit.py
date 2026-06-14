"""Campo de fecha: QDateEdit con calendario desplegable + escritura manual.

Reemplaza CTkDateInput (los 3 entries DD/MM/AAAA). Ventajas nativas:
- Se puede tipear la fecha a mano (click simple en una seccion, Tab entre dia/mes/anio) Y abrir el calendario.
- Nunca acepta fechas invalidas (no hay 32 de mes): validacion de formato gratis.

Arranca con una fecha real por defecto (NO estado vacio): usar setSpecialValueText
para fingir "vacio" rompia la edicion fluida (lo tipeado se iba al final y se
descartaba al perder foco). Con una fecha real, click+tipeo+Tab funcionan nativo.

Sincroniza con las 3 ObservableVar (dia/mes/anio) del AppState para mantener el
contrato con ControladorPrecios (que escucha fecha_*_completa via los traces de AppState).
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QDateEdit
from PySide6.QtCore import QDate, Signal, Qt
from PySide6.QtGui import QTextCharFormat, QColor, QBrush


class QtDateField(QWidget):
    """QDateEdit etiquetado que sincroniza con dia/mes/anio ObservableVar.

    Args:
        label: texto del label.
        day_var, month_var, year_var: ObservableVar (StringVar) componentes de fecha.
        default_offset_days: dias desde hoy para la fecha por defecto (0=hoy, 1=mañana).
        on_change: callback opcional() cuando cambia la fecha (para validacion cruzada).
    """

    dateChanged = Signal(object)   # emite la QDate seleccionada

    def __init__(self, label, day_var, month_var, year_var,
                 default_offset_days=0, on_change=None, highlight_color="#2563EB", parent=None):
        super().__init__(parent)
        self._day, self._month, self._year = day_var, month_var, year_var
        self._default_offset = default_offset_days
        self._on_change = on_change
        self._highlight_color = highlight_color
        self._syncing = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        lbl = QLabel(label)
        lbl.setObjectName("fieldLabel")
        lay.addWidget(lbl)

        self.edit = QDateEdit()
        self.edit.setDisplayFormat("dd/MM/yyyy")
        self.edit.setCalendarPopup(True)            # boton de calendario desplegable
        self.edit.setMinimumDate(QDate(2000, 1, 1))
        self.edit.setMaximumDate(QDate(2100, 12, 31))
        self.edit.setDate(self._default_date())     # arranca con fecha real
        # Ensanchar el popup del calendario y preparar el resaltado del dia seleccionado
        cal = self.edit.calendarWidget()
        if cal is not None:
            cal.setMinimumWidth(280)
            # Formato para pintar el dia seleccionado en azul (QSS no lo hace fiable)
            self._sel_fmt = QTextCharFormat()
            self._sel_fmt.setBackground(QBrush(QColor(self._highlight_color)))
            self._sel_fmt.setForeground(QBrush(QColor("#FFFFFF")))
            self._empty_fmt = QTextCharFormat()
        lay.addWidget(self.edit)

        self.edit.dateChanged.connect(self._on_edit_changed)
        # Sembrar las ObservableVar con el valor inicial + resaltar dia inicial
        self._write_vars(self.edit.date())
        self._highlight(self.edit.date())

    def _default_date(self) -> QDate:
        return QDate.currentDate().addDays(self._default_offset)

    def date(self):
        """Devuelve la QDate actual (siempre hay una)."""
        return self.edit.date()

    def set_minimum(self, qdate):
        """Fija la fecha minima seleccionable (para validar salida > entrada)."""
        self.edit.setMinimumDate(qdate)

    def clear(self):
        """Vuelve a la fecha por defecto (hoy/mañana)."""
        self._syncing = True
        self.edit.setMinimumDate(QDate(2000, 1, 1))
        self.edit.setDate(self._default_date())
        self._syncing = False
        self._write_vars(self.edit.date())

    def _on_edit_changed(self, qdate):
        if self._syncing:
            return
        self._write_vars(qdate)
        self._highlight(qdate)
        self.dateChanged.emit(qdate)
        if self._on_change:
            self._on_change()

    def _highlight(self, qdate):
        """Pinta el dia seleccionado en azul en el popup del calendario."""
        cal = self.edit.calendarWidget()
        if cal is None:
            return
        # Limpiar el resaltado anterior y aplicar el nuevo
        if getattr(self, "_last_highlight", None) is not None:
            cal.setDateTextFormat(self._last_highlight, self._empty_fmt)
        cal.setDateTextFormat(qdate, self._sel_fmt)
        self._last_highlight = qdate

    def _write_vars(self, qdate):
        """Descompone la fecha en dia/mes/anio ObservableVar."""
        self._day.set(f"{qdate.day():02d}")
        self._month.set(f"{qdate.month():02d}")
        self._year.set(str(qdate.year()))
