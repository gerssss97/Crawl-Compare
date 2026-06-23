"""Constantes de dimensión Qt-específicas del design system.

Fuente única de verdad para tamaños, alturas y configuración visual.
Ningún widget ni el stylesheet hardcodea estos valores directamente.

Para colores: UI_qt/styles/palette.py
Para spacing/tipografía compartidos: UI/styles/spacing.py y typography.py
"""

# ---------------------------------------------------------------------------
# Ventana principal
# ---------------------------------------------------------------------------
WINDOW_DEFAULT_W = 1280
WINDOW_DEFAULT_H = 800
WINDOW_MIN_W = 900
WINDOW_MIN_H = 600

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
HEADER_HEIGHT = 60
HEADER_BTN_SIZE = 34      # botones icono del header (gear, theme toggle)

# ---------------------------------------------------------------------------
# Componentes / stylesheet
# ---------------------------------------------------------------------------
INPUT_HEIGHT = 26          # min-height de QLineEdit, QComboBox, QDateEdit
BUTTON_HEIGHT_PRIMARY = 44 # min-height del botón de acción principal
STEPPER_HEIGHT = 34        # min-height del widget QtSpinStepper
MESSAGEBOX_BTN_MIN_W = 70  # min-width de botones en QMessageBox

# ---------------------------------------------------------------------------
# Ícono de la aplicación
# ---------------------------------------------------------------------------
APP_ICON_GRAPHIC_PX = 22   # tamaño del gráfico renderizado en el header
APP_ICON_CANVAS_PX = 28    # canvas del QLabel que lo contiene
APP_ICON_CANVAS_OFFSET = 3 # offset del gráfico dentro del canvas (breathing room)
APP_ICON_TINT = "#DDD5C8"  # color cremita sobre el header oscuro

APP_WIN_ICON_PX = 32       # pixmap base para QApplication.setWindowIcon
APP_WIN_ICON_PAD_PX = 12   # padding derecho transparente (gap en OS title bar)
