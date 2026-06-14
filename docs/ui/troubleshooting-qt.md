# Troubleshooting PySide6 / Qt

> Problemas conocidos de la migración a PySide6 (ver `docs/features/plan-migracion-gui.md`).

---

## `ImportError: DLL load failed while importing QtCore` (WinError 127) en env conda

**Síntoma**: `from PySide6.QtCore import ...` falla con
`ImportError: DLL load failed while importing QtCore: No se encontró el proceso especificado`
(WinError 127 = `ERROR_PROC_NOT_FOUND`). `import PySide6` a secas funciona, pero cualquier submódulo C++ (`QtCore`, `QtGui`, `QtWidgets`) rompe.

**Causa raíz**: choque de versiones de **ICU** entre conda y el wheel de pip de PySide6.
- `Qt6Core.dll` importa `icuuc.dll` (confirmado parseando la import table del PE).
- El wheel de pip de PySide6 **no trae su propia ICU**.
- El env conda ya tiene `icuuc.dll` (en `envs/<env>/Library/bin`) de **otra versión de ICU** (ej. ICU 78), metida por otra dependencia conda.
- El loader de Windows agarra esa ICU de conda, que no exporta los símbolos que Qt 6.11 espera → faltan entrypoints → WinError 127.

**Lo que NO era** (descartado durante el diagnóstico):
- No era falta de DLLs de PySide6 (estaban las 161).
- No era otro Qt/PyQt en conflicto (no había).
- No era el DLL search path (fallaba incluso con `os.add_dll_directory`).
- No era el VC++ Redistributable (estaba en 14.44.x, sobra para Qt 6.11).

**Solución**: instalar PySide6 desde **conda-forge**, NO desde pip. conda-forge compila
PySide6 contra la misma ICU del resto del env, eliminando el choque.

```bash
# 1. Desinstalar el wheel de pip primero (si está) para que no se pisen
python -m pip uninstall -y PySide6 PySide6_Essentials PySide6_Addons shiboken6
# 2. Instalar desde conda-forge
conda install -n crawler -c conda-forge pyside6 -y
```

Verificación:
```bash
"<env>/python.exe" -c "from PySide6.QtWidgets import QApplication; print('OK')"
```

**Implicación para el deploy (Fase 7)**: PyInstaller tiene que empaquetar la ICU correcta
(la de conda-forge). Verificar en el build que `icuuc*.dll` incluida sea la compatible con Qt,
no que arrastre otra del sistema.

---

## Resultado del GATE de resize (Fase 0) — 2026-06-10

Spike `Hoteles/UI_qt/spike_resize.py` (layout 2-columnas real, QSS desde Colors/Spacing),
medido con el mismo método que `.claude/skills/scripts/resize_probe.py`:

| Métrica | CustomTkinter | PySide6 6.11.0 |
|---|---|---|
| avg/frame | ~1000ms | **18.2ms** |
| peor frame | ~2000ms | **43.7ms** |

~55x más rápido en promedio. GATE (<100ms/frame) superado. Migración validada técnicamente.

---

## Rectángulo de fondo feo detrás de QLabel / QPushButton (sobre header oscuro)

**Síntoma**: los `QLabel` (título, nombre del Excel) muestran un rectángulo con el color de
fondo de la app detrás del texto, que resalta feo sobre el header oscuro.

**Causa**: una regla `QWidget { background-color: ... }` en el QSS. En Qt `QLabel` y
`QPushButton` SON `QWidget`, así que heredan ese `background-color`. Sobre un contenedor
de distinto color (header oscuro) el fondo heredado del label canta.

**Solución**: NO pintar `background-color` en el selector genérico `QWidget`. Pintar el
fondo solo en contenedores concretos (`QMainWindow`, `#header`, `#card`...) y declarar
`QLabel {{ background: transparent; }}` explícito. Aplicado en `UI_qt/styles/theme.py`.

---

## `ModuleNotFoundError: No module named 'UI_qt'` al ejecutar un archivo directo

**Síntoma**: `python UI_qt/interfaz_qt.py` falla con ModuleNotFoundError, pero importado
como módulo anda.

**Causa**: el `sys.path.insert` que agrega `Hoteles/` al path estaba DESPUÉS de los
imports de `UI_qt.*` (en el bloque `if __name__ == "__main__"`). Los imports del tope
corren primero, antes de que el path esté seteado.

**Solución**: poner el bootstrap de path en el TOPE del archivo (antes de importar
`UI_qt.*`), guardado por `if __package__ in (None, ""):` para que solo actúe en ejecución
directa, no como módulo. Patrón a respetar en todos los archivos ejecutables de `UI_qt/`.

---

## Resultado de Fase 2 (shell + estilo) — 2026-06-10

`Hoteles/UI_qt/interfaz_qt.py` (`MainWindow`): QMainWindow + header + 2 columnas 65/35,
QSS dual-mode desde `UI_qt/styles/theme.py` (paletas light/dark generadas desde
Spacing/Typography), sombras de card vía `QGraphicsDropShadowEffect`, toggle de tema en vivo.
Cableada al AppState v2. Resize sigue fluido. Paneles internos = placeholders (Fases 3-4).

---

## SVG en data URI dentro del QSS no se renderiza (flecha invisible)

**Síntoma**: una `image: url("data:image/svg+xml;...")` en QSS (ej. `QComboBox::down-arrow`)
no muestra nada. El área es clickeable pero la flecha es invisible. Probado con data URI
`utf8,` Y con `base64,`: ninguno funciona.

**Diagnóstico**: poner `background:#ff0000` (color sólido) en el mismo `::down-arrow` SÍ
muestra un cuadrado → el subcontrol y su posición funcionan; el problema es solo la imagen
SVG. Causa: en este entorno conda PySide6 no resuelve SVG embebido en QSS (plugin `qsvg`
no aplica a ese caso).

**Solución**: generar el icono como **PNG en runtime con QPainter** y referenciarlo por path
en el QSS (`url("C:/.../chevron.png")`, con forward slashes). PNG por path es 100% confiable,
sin depender de plugins. Implementado en `UI_qt/styles/icons_gen.py` (cachea en `_generated/`,
ignorado por git). **Implicación deploy (Fase 7)**: o se incluye el plugin qsvg en el bundle,
o se sigue con PNG generado (más seguro).

---

## El día seleccionado del QCalendarWidget no se resalta vía QSS

**Síntoma**: `selection-background-color` en `QCalendarWidget QAbstractItemView` no pinta
el día seleccionado de forma fiable.

**Solución**: aplicar `QTextCharFormat` con `setDateTextFormat(fecha, fmt)` desde código
(no QSS). Implementado en `QtDateField._highlight()`: limpia el formato del día anterior y
pinta el nuevo con el color de acento del tema. El hover de celda NO se recupera (limitación
del view del calendario); se acepta, el resaltado de selección da feedback suficiente.

---

## Resultado de Fase 3 (formulario) — 2026-06-11

`UI_qt/widgets/`: `QtLabeledCombo` (QComboBox, reemplaza 510 líneas de CTkCustomDropdown),
`QtDateField` (QDateEdit con calendario+escritura manual, validación de fecha gratis,
arranca con fecha real por defecto -hoy/mañana- porque setSpecialValueText rompía la edición),
`QtFormReserva` (hotel/edificio dinámico/habitación), `QtFormFechas` (fechas con validación
cruzada preventiva vía setMinimumDate + consolidación de fecha_*_completa).
Cableado a ControladorHotel/Precios/Validacion reutilizados. Excel real carga y puebla combos.

---

## UnicodeEncodeError ('charmap' can't encode '→') durante el scraping

**Síntoma**: el scraping "falla" con `'charmap' codec can't encode character '→'`,
capturado como "ERROR en periodo N". El scraping en sí funcionó (LiteLLM/Groq completó).

**Causa**: el Core (`comparador_multiperiodo.py`) hace `print(f"→ ...")` con la flecha
Unicode `→`. Al correr la app Qt desde la consola de Windows (cp1252 por default), ese
print revienta. En el .exe no pasaba porque `error_logger.py` redirige stdout a UTF-8.
NO es un bug de la migración Qt; es encoding de consola preexistente del Core.

**Solución**: reconfigurar stdout/stderr a UTF-8 al arrancar (en el bootstrap de
`interfaz_qt.py`, antes de imports que impriman):
```python
for _stream in (sys.stdout, sys.stderr):
    try: _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError): pass
```
No toca el Core. Replica lo que hace el logger del .exe.

---

## Threading del scraping en Qt (EventBridge, NO tocar widgets desde otro hilo)

`ControladorComparacion` corre el scraping en `threading.Thread` y emite eventos al
EventBus DESDE ese hilo. En Qt, tocar widgets desde un hilo != GUI crashea.
**Solución implementada**: `UI_qt/state/event_bridge.py` (`EventBridge`, QObject) escucha
el EventBus y re-emite como Qt Signals. Los signals cruzan de hilo con `QueuedConnection`
automático → los slots corren en el hilo de la GUI. Los modales conectan a los signals del
bridge, NO al EventBus directo. No se tocó el controlador (sigue con threading.Thread).

---

## Resultado de Fase 5+6 (modales + threading) — 2026-06-11

Flujo central de comparación funcionando en PySide6: botón Ejecutar → scraping en hilo
→ modal (`QtResultadosModal`, QDialog no-modal por comparison_id, soporta paralelas) con
progreso en vivo + tabla de resultados (QTextBrowser/HTML) + email. Sin congelar la UI.
Modales secundarios pendientes: Historial, Config.
