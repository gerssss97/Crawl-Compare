"""Combo con label arriba, sincronizado con una ObservableVar del AppState.

Soporta typeahead: el usuario puede escribir para filtrar opciones (MatchContains,
case-insensitive) o usar la flechita para ver y elegir del listado completo.

El popup container (QComboBoxPrivateContainer) se redondea via WA_TranslucentBackground +
FramelessWindowHint aplicados en __init__ (antes del native handle), que es la unica
forma confiable en Qt6/Windows. setMask falla porque el container tiene el QComboBox
como parent Qt y el color :focus sangra en las areas recortadas.

Click en el line edit abre el completer popup (no el native dropdown) para evitar
el ciclo WM_ACTIVATE que Qt genera al crear ventanas Qt::Popup desde codigo externo.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QCompleter, QFrame, QApplication
from PySide6.QtCore import Qt, QStringListModel, QObject, QEvent, QTimer
from UI_qt.styles.theme import LIGHT
from UI.styles import Spacing

_R = Spacing.RADIUS_MD
_BORDER = LIGHT.border
_SURFACE = LIGHT.surface


class _RoundedCombo(QComboBox):
    """QComboBox cuyo popup container tiene esquinas redondeadas.

    Los flags (FramelessWindowHint, WA_TranslucentBackground) se aplican
    en __init__ antes de que Qt cree el native handle del container. Aplicarlos
    en showPopup() es tarde: el handle ya existe y los flags son ignorados.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._configure_popup()

    def _configure_popup(self):
        container = self.view().parentWidget()
        if container is None:
            return
        container.setWindowFlags(
            Qt.WindowType.Popup |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )
        container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        container.setAutoFillBackground(False)
        container.setFrameShape(QFrame.Shape.NoFrame)
        QApplication.setEffectEnabled(Qt.UIEffect.UI_AnimateCombo, False)

    def showPopup(self):
        super().showPopup()
        container = self.view().parentWidget()
        if container is None:
            return
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {_SURFACE};
                border: 1px solid {_BORDER};
                border-radius: {_R}px;
            }}
        """)


class _LineEditClickFilter(QObject):
    """Abre el completer popup al hacer clic en el line edit.

    Usa completer.complete() en lugar de showPopup() para evitar el ciclo
    WM_ACTIVATE: el completer popup no roba el foco del line edit, por lo que
    Windows no genera mensajes de activacion que Qt traduciria en hidePopup().
    """

    def __init__(self, combo):
        super().__init__(combo)
        self._combo = combo

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            native_open = self._combo.view().isVisible()
            completer_open = self._combo.completer().popup().isVisible()
            if not native_open and not completer_open:
                def _open():
                    self._combo.completer().setCompletionPrefix("")
                    self._combo.completer().complete()
                QTimer.singleShot(0, _open)
        return False


class _DropdownKeyFilter(QObject):
    """Event filter en combo.view(): redirige keypresses al line edit mientras
    el dropdown nativo esta abierto, para que escribir filtre el listado."""

    def __init__(self, combo):
        super().__init__(combo)
        self._combo = combo

    def eventFilter(self, obj, event):
        if event.type() != QEvent.Type.KeyPress:
            return False
        key = event.key()
        text = event.text()
        line = self._combo.lineEdit()
        completer = self._combo.completer()

        if text and text.isprintable():
            self._combo.hidePopup()
            new_text = line.text() + text
            line.setText(new_text)
            line.setCursorPosition(len(new_text))
            completer.setCompletionPrefix(new_text)
            completer.complete()
            return True

        if key == Qt.Key.Key_Backspace:
            self._combo.hidePopup()
            new_text = line.text()[:-1]
            line.setText(new_text)
            line.setCursorPosition(len(new_text))
            completer.setCompletionPrefix(new_text)
            completer.complete()
            return True

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

        self._model = QStringListModel([])
        self._completer = QCompleter(self._model)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.combo.setCompleter(self._completer)
        self._configure_completer_popup()

        # Click en el field abre el completer popup (no el native dropdown)
        self.combo.lineEdit().installEventFilter(_LineEditClickFilter(self.combo))
        # Redirige keypresses al line edit cuando el dropdown nativo esta abierto
        self.combo.view().installEventFilter(_DropdownKeyFilter(self.combo))

        # Seleccion desde el dropdown nativo (flechita)
        self.combo.activated.connect(self._on_activated)
        # Seleccion desde el popup del completer (click o escritura)
        self._completer.activated[str].connect(self._on_completer_activated)
        # Validacion al perder foco o presionar Enter
        self.combo.lineEdit().editingFinished.connect(self._on_editing_finished)

        lay.addWidget(self.combo)

        self._var.trace_add('write', self._on_var_changed)

    def _configure_completer_popup(self):
        popup = self._completer.popup()
        popup.setWindowFlags(
            Qt.WindowType.Popup |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )
        popup.setStyleSheet(f"""
            QListView {{
                background-color: {_SURFACE};
                border: 1px solid {_BORDER};
                border-radius: {_R}px;
                outline: none;
            }}
        """)

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
