"""Splash screen de arranque del .exe usando QSplashScreen de PySide6."""
from PySide6.QtWidgets import QApplication, QSplashScreen, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont

_BG = "#F8FAFC"
_TITLE_FG = "#1E293B"
_SUBTITLE_FG = "#64748B"
_BAR_FG = "#2563EB"
_BAR_BG = "#E2E8F0"

_WIDTH = 400
_HEIGHT = 200
_BAR_H = 4
_BAR_Y = _HEIGHT - 20


def _make_pixmap(status: str, progress: float) -> QPixmap:
    """Renderiza el contenido del splash en un QPixmap.

    progress: valor entre 0.0 y 1.0 para la barra animada.
    """
    px = QPixmap(_WIDTH, _HEIGHT)
    px.fill(QColor(_BG))

    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Título
    font_title = QFont("Segoe UI", 18, QFont.Weight.Bold)
    p.setFont(font_title)
    p.setPen(QColor(_TITLE_FG))
    p.drawText(0, 28, _WIDTH, 36, Qt.AlignmentFlag.AlignHCenter, "Crawl Compare")

    # Subtítulo
    font_sub = QFont("Segoe UI", 10)
    p.setFont(font_sub)
    p.setPen(QColor(_SUBTITLE_FG))
    p.drawText(0, 68, _WIDTH, 24, Qt.AlignmentFlag.AlignHCenter, "Comparador de Precios de Hoteles")

    # Estado dinámico
    p.setPen(QColor(_TITLE_FG))
    p.drawText(0, 110, _WIDTH, 24, Qt.AlignmentFlag.AlignHCenter, status)

    # Barra de progreso indeterminada (segmento que se mueve)
    bar_x = 40
    bar_w = _WIDTH - 80
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(_BAR_BG))
    p.drawRoundedRect(bar_x, _BAR_Y, bar_w, _BAR_H, 2, 2)

    # Segmento animado: ocupa 30% del ancho, se mueve según progress
    seg_w = int(bar_w * 0.30)
    travel = bar_w - seg_w
    seg_x = bar_x + int(travel * progress)
    p.setBrush(QColor(_BAR_FG))
    p.drawRoundedRect(seg_x, _BAR_Y, seg_w, _BAR_H, 2, 2)

    p.end()
    return px


class SplashScreen:
    """QSplashScreen con barra de progreso animada y label de estado.

    Interfaz compatible con el splash anterior (update_status / close).
    """

    def __init__(self):
        self._status = "Iniciando..."
        self._progress = 0.0
        self._direction = 1
        self._step = 0.02

        self._splash = QSplashScreen()
        self._splash.setWindowFlags(
            Qt.WindowType.SplashScreen |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )
        self._splash.setFixedSize(_WIDTH, _HEIGHT)
        self._splash.show()
        self._render()

        # Timer de animación a ~30fps
        self._timer = QTimer()
        self._timer.timeout.connect(self._animate)
        self._timer.start(33)

        QApplication.processEvents()

    def _render(self) -> None:
        px = _make_pixmap(self._status, self._progress)
        self._splash.setPixmap(px)
        self._splash.repaint()

    def _animate(self) -> None:
        self._progress += self._step * self._direction
        if self._progress >= 1.0:
            self._progress = 1.0
            self._direction = -1
        elif self._progress <= 0.0:
            self._progress = 0.0
            self._direction = 1
        self._render()
        QApplication.processEvents()

    def update_status(self, mensaje: str) -> None:
        """Actualiza el label de estado y fuerza redibujado."""
        self._status = mensaje
        try:
            print(f"[startup] {mensaje}", flush=True)
        except Exception:
            pass
        self._render()
        QApplication.processEvents()

    def close(self) -> None:
        """Para la animación y cierra el splash."""
        self._timer.stop()
        self._splash.close()
