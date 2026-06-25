"""Combo con label arriba, sincronizado con una ObservableVar del AppState.

Soporta typeahead: el usuario puede escribir para filtrar opciones (MatchContains,
case-insensitive). Tanto el click en el input como la flechita abren el mismo
popup del completer — un solo sistema visual consistente.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QCompleter
from PySide6.QtCore import Qt, QStringListModel, QObject, QEvent, QTimer
from UI_qt.styles import Spacing


class _RoundedCombo(QComboBox):
    """QComboBox que redirige showPopup() al completer en vez del popup nativo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._open_popup_fn = None

    def showPopup(self):
        if self._open_popup_fn:
            self._open_popup_fn()


class _LineEditClickFilter(QObject):
    """Abre el completer popup al hacer click en el line edit.

    Usa completer.complete() en lugar de showPopup() para evitar el ciclo
    WM_ACTIVATE: el completer popup no roba el foco del line edit, por lo que
    Windows no genera mensajes de activacion que Qt traduciria en hidePopup().
    """

    def __init__(self, open_fn):
        super().__init__()
        self._open = open_fn

    def eventFilter(self, _obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            QTimer.singleShot(0, self._open)
        return False


class QtLabeledCombo(QWidget):
    """QComboBox editable con label, atado a una ObservableVar.

    Args:
        label: texto del label.
        variable: ObservableVar (StringVar) que refleja la seleccion.
        on_change: callback opcional(valor) al confirmar una seleccion valida.
    """

    def __init__(self, label, variable, on_change=None, parent=None):
        super().__init__(parent)
        self._var = variable
        self._on_change = on_change
        self._syncing = False
        self._values = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        lbl = QLabel(label)
        lbl.setObjectName("fieldLabel")
        lay.addWidget(lbl)

        self.combo = _RoundedCombo()
        self.combo.setEditable(True)
        self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo.setMaxVisibleItems(Spacing.DROPDOWN_MAX_VISIBLE)

        self._model = QStringListModel([])
        self._completer = QCompleter(self._model)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.combo.setCompleter(self._completer)
        self._configure_completer_popup()
        self.combo._open_popup_fn = self._open_completer_popup
        self._click_filter = _LineEditClickFilter(self._open_completer_popup)
        self.combo.lineEdit().installEventFilter(self._click_filter)

        # Seleccion desde el dropdown nativo (flechita)
        self.combo.activated.connect(self._on_activated)
        # Seleccion desde el popup del completer (typeahead)
        self._completer.activated[str].connect(self._on_completer_activated)
        # Validacion al perder foco o presionar Enter
        self.combo.lineEdit().editingFinished.connect(self._on_editing_finished)

        lay.addWidget(self.combo)

        self._var.trace_add('write', self._on_var_changed)

    def _open_completer_popup(self):
        popup = self._completer.popup()
        if popup.isVisible():
            return
        self._completer.setCompletionPrefix("")
        self._completer.complete()

    def _configure_completer_popup(self):
        popup = self._completer.popup()
        popup.setWindowFlags(
            Qt.WindowType.Popup |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )
        popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        popup.viewport().setObjectName("completerPopupViewport")
        popup.setObjectName("completerPopup")
        self._completer.setMaxVisibleItems(Spacing.DROPDOWN_MAX_VISIBLE)

    def set_values(self, valores):
        """Puebla el combo y actualiza el completer."""
        self._syncing = True
        self._values = list(valores)
        self.combo.clear()
        self.combo.addItem("")
        self.combo.addItems(self._values)
        self.combo.setCurrentIndex(0)
        self._model.setStringList(self._values)
        self._syncing = False

    # ---- seleccion desde flechita ----

    def _on_activated(self, index):
        texto = self.combo.itemText(index)
        self._accept(texto)

    # ---- seleccion desde popup del completer ----

    def _on_completer_activated(self, texto):
        self._accept(texto)

    # ---- blur / Enter ----

    def _on_editing_finished(self):
        if self._syncing:
            return
        texto = self.combo.currentText().strip()
        match = next((v for v in self._values if v.lower() == texto.lower()), None)
        if match:
            self._accept(match)
        elif texto:
            self._syncing = True
            self.combo.setCurrentIndex(0)
            self._var.set("")
            self._syncing = False

    # ---- nucleo: acepta un valor valido ----

    def _accept(self, texto):
        """Normaliza case, setea la var y dispara on_change si el valor cambio."""
        if self._syncing:
            return
        match = next((v for v in self._values if v.lower() == texto.strip().lower()), None)
        if not match or match == self._var.get():
            return
        self._syncing = True
        idx = self.combo.findText(match)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)
        self._var.set(match)
        self._syncing = False
        if self._on_change:
            self._on_change(match)

    # ---- var -> combo (set() externo) ----

    def _on_var_changed(self, *_args):
        if self._syncing:
            return
        valor = self._var.get()
        idx = self.combo.findText(valor)
        if idx >= 0:
            self._syncing = True
            self.combo.setCurrentIndex(idx)
            self._syncing = False