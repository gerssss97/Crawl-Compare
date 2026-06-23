# Split UI_qt/styles — Separación de responsabilidades

## Problema

`UI_qt/styles/theme.py` acumula tres responsabilidades distintas mezcladas:
- Definición de tokens de color (`Palette` dataclass + `LIGHT`/`DARK`)
- Generación del QSS global (`build_qss` — ~230 líneas)
- Valores hardcodeados embebidos en las strings del QSS (alturas, anchos)

El layer CTk ya tiene esta separación limpia en `UI/styles/` (colors, spacing, typography, button_styles).
La regla del proyecto es: **sin magic numbers en widgets ni en el stylesheet — todo va en constantes nombradas**.

## Solución

Dividir `theme.py` en tres archivos con responsabilidad única, espejando `UI/styles/`:

```
UI_qt/styles/
  palette.py      ← Palette dataclass + LIGHT, DARK, PALETTES (solo datos)
  constants.py    ← Tamaños Qt-específicos: ventana, header, inputs, íconos
  stylesheet.py   ← build_qss() que importa de los dos anteriores
  theme.py        ← shim de re-exportación (backward compat)
```

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `UI_qt/styles/palette.py` | Nuevo — Palette dataclass + instancias |
| `UI_qt/styles/constants.py` | Nuevo — constantes de dimensión + ícono |
| `UI_qt/styles/stylesheet.py` | Nuevo — build_qss() |
| `UI_qt/styles/theme.py` | Shim de re-export |
| `UI_qt/styles/__init__.py` | Re-exporta todo desde los nuevos módulos |
| `UI_qt/widgets/qt_labeled_combo.py` | Import LIGHT desde `UI_qt.styles` |
| `UI_qt/interfaz_qt.py` | Usa HEADER_HEIGHT, HEADER_BTN_SIZE, WINDOW_* |
| `main.py` | Usa APP_WIN_ICON_PX, APP_WIN_ICON_PAD_PX |
| `CLAUDE.md` | Agrega regla de no magic numbers |
| `docs/desarrollo/convenciones.md` | Agrega sección de design tokens Qt |

## Constantes extraídas a constants.py

```python
# Ventana principal
WINDOW_DEFAULT_W = 1280
WINDOW_DEFAULT_H = 800
WINDOW_MIN_W = 900
WINDOW_MIN_H = 600

# Header
HEADER_HEIGHT = 60
HEADER_BTN_SIZE = 34

# Componentes
INPUT_HEIGHT = 26
BUTTON_HEIGHT_PRIMARY = 44
STEPPER_HEIGHT = 34
MESSAGEBOX_BTN_MIN_W = 70

# Ícono de la aplicación (header + ventana OS)
APP_ICON_GRAPHIC_PX = 22
APP_ICON_CANVAS_PX = 28
APP_ICON_CANVAS_OFFSET = 3
APP_ICON_TINT = "#DDD5C8"
APP_WIN_ICON_PX = 32
APP_WIN_ICON_PAD_PX = 12
```
