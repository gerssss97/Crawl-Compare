"""Widget stepper [-] value [+] para cantidades enteras con edición por teclado."""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QLineEdit, QSizePolicy
from PySide6.QtCore import Qt, Signal, QTimer, QObject, QEvent
from PySide6.QtGui import QIntValidator


class _FocusFilter(QObject):
    """Propaga los eventos de foco del QLineEdit al QFrame contenedor,
    para que el frame pueda mostrar el borde azul cuando el input está activo."""

    def __init__(self, frame: QFrame):
        super().__init__(frame)
        self._frame = frame

    def eventFilter(self, _, event):
        t = event.type()
        if t in (QEvent.FocusIn, QEvent.FocusOut):
            focused = t == QEvent.FocusIn
            self._frame.setProperty("focused", focused)
            self._frame.style().unpolish(self._frame)
            self._frame.style().polish(self._frame)
        return False


class QtSpinStepper(QFrame):

    value_changed = Signal(int)

    def __init__(self, min_val: int = 0, max_val: int = 20, default: int = 0,
                 step: int = 1, parent=None):
        super().__init__(parent)
        self.setObjectName("spinStepper")
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self._min = min_val
        self._max = max_val
        self._val = max(min_val, min(max_val, default))
        self._step = max(1, step)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 0, 6, 0)
        lay.setSpacing(4)

        self._btn_minus = QPushButton("−")
        self._btn_minus.setObjectName("stepperBtn")
        self._btn_minus.setFixedSize(22, 30)
        self._btn_minus.setFocusPolicy(Qt.NoFocus)
        self._btn_minus.clicked.connect(self._dec)

        self._lbl = QLineEdit(str(self._val))
        self._lbl.setObjectName("stepperValue")
        self._lbl.setAlignment(Qt.AlignCenter)
        self._lbl.setFixedWidth(48)
        self._lbl.setValidator(QIntValidator(min_val, max_val))
        self._lbl.editingFinished.connect(self._on_text_edited)
        self._lbl.installEventFilter(_FocusFilter(self))

        self._btn_plus = QPushButton("+")
        self._btn_plus.setObjectName("stepperBtn")
        self._btn_plus.setFixedSize(22, 30)
        self._btn_plus.setFocusPolicy(Qt.NoFocus)
        self._btn_plus.clicked.connect(self._inc)

        lay.addWidget(self._btn_minus)
        lay.addWidget(self._lbl)
        lay.addWidget(self._btn_plus)

    def _dec(self):
        if self._val > self._min:
            self._val = max(self._min, self._val - self._step)
            self._lbl.setText(str(self._val))
            self.value_changed.emit(self._val)
        self._flash(self._btn_minus)

    def _inc(self):
        if self._val < self._max:
            self._val = min(self._max, self._val + self._step)
            self._lbl.setText(str(self._val))
            self.value_changed.emit(self._val)
        self._flash(self._btn_plus)

    def _on_text_edited(self):
        try:
            val = int(self._lbl.text())
        except ValueError:
            val = self._val
        self._val = max(self._min, min(self._max, val))
        self._lbl.setText(str(self._val))
        self.value_changed.emit(self._val)

    def _flash(self, btn):
        btn.setProperty("active", True)
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        QTimer.singleShot(50, lambda: self._unflash(btn))

    def _unflash(self, btn):
        btn.setProperty("active", False)
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def value(self) -> int:
        return self._val

    def setValue(self, val: int):
        self._val = max(self._min, min(self._max, val))
        self._lbl.setText(str(self._val))
