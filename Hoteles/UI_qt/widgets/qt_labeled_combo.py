"""Combo con label arriba, sincronizado con una ObservableVar del AppState.

Reemplaza CTkLabeledComboBox + CTkCustomDropdown (510 lineas de workaround) por
un QComboBox nativo. No editable (solo seleccion). Mantiene la variable de estado
en sync en ambos sentidos: seleccion del usuario -> var, y var.set() externo -> combo.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox


class QtLabeledCombo(QWidget):
    """QComboBox con label, atado a una ObservableVar.

    Args:
        label: texto del label.
        variable: ObservableVar (StringVar) que refleja la seleccion.
        on_change: callback opcional(valor) al cambiar la seleccion por el usuario.
    """

    def __init__(self, label, variable, on_change=None, parent=None):
        super().__init__(parent)
        self._var = variable
        self._on_change = on_change
        self._syncing = False   # evita recursion var<->combo

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        lbl = QLabel(label)
        lbl.setObjectName("fieldLabel")
        lay.addWidget(lbl)

        self.combo = QComboBox()
        self.combo.setEditable(False)
        lay.addWidget(self.combo)

        # combo -> variable (+ callback)
        self.combo.currentTextChanged.connect(self._on_combo_changed)
        # variable -> combo (cuando alguien hace var.set() desde afuera, ej. restaurar historial)
        self._var.trace_add('write', self._on_var_changed)

    def set_values(self, valores):
        """Puebla el combo. Limpia primero. Inserta un item vacio inicial para no autoseleccionar."""
        self._syncing = True
        self.combo.clear()
        self.combo.addItem("")          # estado "nada seleccionado"
        self.combo.addItems(list(valores))
        self.combo.setCurrentIndex(0)
        self._syncing = False

    def _on_combo_changed(self, texto):
        if self._syncing:
            return
        self._syncing = True
        self._var.set(texto)
        self._syncing = False
        if self._on_change and texto:
            self._on_change(texto)

    def _on_var_changed(self, *_args):
        if self._syncing:
            return
        valor = self._var.get()
        idx = self.combo.findText(valor)
        if idx >= 0:
            self._syncing = True
            self.combo.setCurrentIndex(idx)
            self._syncing = False
