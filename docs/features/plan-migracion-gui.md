# Plan de Migración GUI: CustomTkinter → PySide6

> Estado: **PROPUESTA — pendiente de aprobación ítem por ítem**
> Fecha: 2026-06-09
> Origen: [HANDOFF.md](../../HANDOFF.md) — el freeze de resize es estructural de CTk (44 `CTkCanvas` rasterizando a software en single-thread Tcl/Tk). El maintainer cerró el issue como "not planned" (CTk #2690).

---

## 0. Decisión de framework: por qué PySide6

### El problema no es GPU, es la arquitectura de render de Tcl/Tk
El freeze medido (avg ~1000ms/frame de resize) viene de que CTk dibuja cada esquina redondeada/borde/fondo de **cada widget** sobre un `tkinter.Canvas` propio, por software, en un único hilo. En el resize se disparan ~67 eventos `<Configure>` y cada canvas se rasteriza de nuevo.

Qt **no hace nada de eso**:
- Scene graph nativo con repintado por **regiones sucias** (solo repinta lo que cambió).
- Layouts (`QHBoxLayout`/`QVBoxLayout`/`QGridLayout`) recalculan geometría en **C++ compilado**, no en Python interpretado.
- No necesita GPU: el salto que resuelve el freeze es **salir de Tcl/Tk single-thread con rasterización manual**.

### Por qué PySide6 y no las otras
| Framework | Resize | Look moderno/dark | .exe | Esfuerzo | Licencia | Veredicto |
|---|---|---|---|---|---|---|
| **PySide6** | ✅ scene graph nativo | ✅ con QSS / qt-material | ⚠️ pesa (~100MB, excluible WebEngine) | 🟡 medio | **LGPL** (cierra fuente gratis) | **ELEGIDO** |
| Flet | ✅ GPU (Flutter) | ✅✅ Material de fábrica | ⚠️ bundler propio | 🟡 medio (paradigma **declarativo** distinto) | Apache 2.0 | Descartado: choca con MVC imperativo actual |
| Dear PyGui | ✅✅ GPU | ❌ look de debug/tooling | ✅ liviano | 🟢 bajo | MIT | Descartado: estética |
| wxPython | ✅ nativo | ❌ look Windows estándar | ✅ | 🟡 | permisiva | Descartado: no moderno |

### Por qué PySide6 encaja con NUESTRA arquitectura
- **Signals & Slots de Qt ≈ nuestro EventBus.** Conceptualmente idéntico. La capa de vista migra de forma natural sin aprender un paradigma reactivo nuevo.
- **Licencia LGPL**: cerrás fuente sin pagar (PyQt6 sería GPL y obligaría a abrir o pagar comercial).
- **Compatibilidad verificada e INSTALADO**: el env conda `crawler` corre **Python 3.12.11**; PySide6 **6.11.1** instalado ahí OK (wheels `abi3`, soportan 3.10+). ⚠️ El Bash tool por defecto usa el Python `base` (3.13.5) — para correr la app hay que usar `C:/Users/German Lucero/anaconda3/envs/crawler/python.exe`. ✅

---

## 1. Hallazgo crítico que corrige el HANDOFF

El HANDOFF (líneas 70-71) afirmaba que **AppState, controladores y EventBus son agnósticos a la UI**. **Eso es parcialmente falso** y hay que saberlo antes de migrar:

| Capa | ¿Acoplada a Tkinter? | Evidencia | Esfuerzo |
|---|---|---|---|
| **Core/** | ❌ NO (limpio) | grep de `tkinter` en Core → 0 matches | Reutilizable tal cual |
| **EventBus** | ❌ NO | `event_bus.py` es pub/sub puro Python | Reutilizable tal cual |
| **Controllers** | ⚠️ POCO | Solo `.get()`, `.set()`, `trace_add()` sobre AppState. 1 `import tkinter` **muerto** en `controlador_comparacion.py:5` | Mínimo — abstraer 3 operaciones |
| **AppState** | ✅ SÍ | `tk.StringVar`, `tk.IntVar`, `trace_add` por todos lados | **Reescribir** (clave) |
| **Components/Views** | ✅ SÍ (100%) | Todo es `ctk.*` / `tk.*` | **Reescribir** (el grueso) |

### La pieza que destraba todo: `ObservableVar`
Los controladores tocan AppState **solo** vía `.get()` / `.set()` / `trace_add('write', cb)`. Si creamos una clase `ObservableVar` con esa **misma API** (respaldada por un `Signal` de Qt internamente), los controladores **no cambian una línea**. Ese es el punto de palanca de toda la migración.

```python
# UI/state/observable.py (nuevo)
from PySide6.QtCore import QObject, Signal

class ObservableVar(QObject):
    changed = Signal(object)
    def __init__(self, value=""):
        super().__init__()
        self._value = value
    def get(self):
        return self._value
    def set(self, v):
        if v != self._value:
            self._value = v
            self.changed.emit(v)
    def trace_add(self, mode, callback):   # firma compatible con tk.Variable
        self.changed.connect(lambda v: callback())
```

Con esto, `AppState` deja de heredar de Tkinter y los controladores quedan intactos.

---

## 2. Inventario de lo que se reescribe (medido, 6064 líneas UI totales)

### Reutilizable sin cambios (Core + infra)
- Todo `Core/`, `Models/`, `ExtractorDatos/`, `ScrawlingChinese/`
- `UI/state/event_bus.py` (79 líneas)
- `UI/controllers/**` (~700 líneas) — salvo borrar el import muerto y verificar `root.after` → `QTimer`
- `UI/services/historial_service.py`, validators

### Reescribir (capa de vista)
Ordenado por complejidad (líneas):

| Archivo | Líneas | Complejidad migración | Equivalente Qt |
|---|---|---|---|
| `interfaz_ctk.py` | 940 | Alta (orquestador) | `QMainWindow` + `QHBoxLayout` |
| `ctk_custom_dropdown.py` | 510 | **Alta** (dropdown custom en Toplevel) | `QComboBox` **nativo** (gratis, resuelve el dolor original) |
| `config_modal.py` | 438 | Media | `QDialog` + `QTabWidget` |
| `resultados_modal.py` | 396 | Media | `QDialog` |
| `vista_resultados.py` | 289 | Media (tk.Text con tags) | `QTextEdit` / `QTableWidget` |
| `ctk_precio_panel.py` | 267 | Media | `QFrame` + layouts |
| `ctk_inline_suggester.py` | 245 | Media | `QCompleter` **nativo** |
| `ctk_periodos_panel.py` | 199 | Media | `QFrame` |
| `ctk_date_input.py` | 189 | Baja | `QDateEdit` **nativo** |
| `historial_modal.py` | 182 | Baja | `QDialog` |
| resto componentes | ~600 | Baja | widgets Qt directos |

**Ganancia colateral**: varios componentes custom que sufriste (dropdown, autocomplete, date input, scrollbar autohide) son **nativos en Qt**. Se borran cientos de líneas de workarounds.

### Estilos (`UI/styles/`)
- `colors.py`, `spacing.py`, `typography.py`: **se reutiliza la paleta** (son constantes), se traduce a **QSS** (CSS de Qt) en vez de pasar kwargs por widget.
- `icons.py`: Feather icons PNG → siguen sirviendo (`QIcon`).

---

## 3. Estrategia de migración: paralela y por fases

Misma estrategia que usaste para CTk (migración sin riesgo, toggle en `main.py`). **No se borra nada hasta que la versión Qt esté validada.**

```python
# main.py
UI_FRAMEWORK = "pyside6"   # "pyside6" | "customtkinter" | "tkinter"
```

### Fase 0 — Spike de validación ✅ COMPLETADA (2026-06-10) — GATE SUPERADO
Prototipo `Hoteles/UI_qt/spike_resize.py`: layout 2 columnas real (form izq + precio/periodos der), QSS generado desde `Colors`/`Spacing`, medido con el mismo método de `resize_probe.py`.

| Métrica | CTk | PySide6 6.11.0 | Mejora |
|---|---|---|---|
| avg/frame | ~1000ms | **18.2ms** | ~55x |
| peor frame | ~2000ms | **43.7ms** | ~46x |

- **GATE (<100ms/frame): SUPERADO con margen.** Migración validada técnicamente.
- Bug de entorno resuelto en el camino: choque de ICU pip vs conda → instalar PySide6 por **conda-forge**, no pip. Ver `docs/ui/troubleshooting-qt.md`.

### Fase 1 — Núcleo desacoplado ✅ COMPLETADA (2026-06-10)
- ✅ `UI_qt/state/observable.py`: `ObservableVar` + subtipos `StringVar`/`IntVar` (Signal de Qt con API de `tk.Variable`). Emite en cada `.set()` como Tk (sin guard de igualdad, decisión deliberada para no alterar semántica).
- ✅ `UI_qt/state/app_state.py`: `AppState` v2 sin Tkinter, API pública idéntica.
- ✅ Borrado el `import tkinter` muerto en `controlador_comparacion.py:5`.
- ✅ **Test headless** `UI_qt/test_fase1_headless.py`: 10/10 checks OK. Los controladores reales (`ControladorPrecios`/`Comparacion`/`Validacion`) se conectan y reaccionan SIN modificarse. **Tesis del plan confirmada con código ejecutable.**
- ⏳ PENDIENTE (se resuelve en Fase 6, no acá): `root.after(...)` → `QTimer.singleShot(...)` y el cruce de hilo del scraping (`threading.Thread` → UI). Es de la capa de vista, no del núcleo; se aborda cuando exista la ventana Qt.

### Diseño visual APROBADO (Figma, 2026-06-10)
Mockup en archivo Figma "Scrawler" (`B2s0j02LH07YYTdCTxTu6t`). Dirección aprobada por el usuario: **dual mode (light + dark)**, QSS-first. Tema: QSS propio desde `colors.py`/`spacing.py` (no qt-material).

**Paletas:**
- Light: bg `#F1F5F9`, surface `#FFFFFF`, border `#E2E8F0`, headerBg `#1E293B`, primary/accent `#2563EB`, inputBg `#F8FAFC`, textPrimary `#1E293B`, textSecondary `#64748B`, textMuted `#94A3B8`.
- Dark: bg `#0F172A`, surface `#1E293B`, border `#334155`, headerBg `#0B1220`, primary `#2563EB`, accent `#60A5FA`, inputBg `#0F172A`, textPrimary `#F1F5F9`, textSecondary `#94A3B8`, textMuted `#64748B`.

**Tokens visuales:** cards con `corner-radius 12px` + sombra sutil (`QGraphicsDropShadowEffect`, light: negro 6% offset y=2 blur=8; dark: negro 25% blur=10). Inputs radius 8px. Botón primario radius 10px, alto 48px. Layout 65/35.

**Dos refinamientos pedidos (NO alcanzaron a entrar en Figma por rate limit; se implementan en código):**

1. **Panel PERÍODOS — filas expandibles (disclosure).** Cada período es una fila con un chevron (`▸`/`▾`) a la izquierda + nombre + precio. Colapsada por defecto. Al expandir, despliega una sub-fila con el **rango completo del período** definido en el Excel (ej. "Rango del período: 01/12/2025 → 15/03/2026"). En Qt: `QToolButton` checkable (o frame clickeable) + sub-`QFrame` que se muestra/oculta con `setVisible()`. La fila expandida lleva borde de acento.

2. **Panel PRECIO — desglose multiperiodo con tramos.** Cuando la reserva cruza varios períodos:
   - Título "PRECIO ESTIMADO" + monto/rango grande (ej. "$ 30.000 – $ 45.000") en color de acento.
   - Subtítulo: "N noches · {fecha_entrada} → {fecha_salida} · cruza M períodos".
   - Separador + "DESGLOSE POR PERÍODO".
   - Una fila por período tocado mostrando: nombre del período + **el tramo de la reserva que cae en ese período** (interpretación B: "Tu tramo: 28/12 → 31/12 (3 noches)") + el precio de ese período.
   - Caso simple (1 período): se omite el desglose, solo monto + "por noche · {período} · {tramo}".

### Fase 2 — Shell + estilo ✅ COMPLETADA (2026-06-10)
- ✅ `UI_qt/interfaz_qt.py` (`MainWindow`): QMainWindow + header (título, Historial, Excel, Cambiar, toggle tema, engranaje) + 2 columnas 65/35 con `QHBoxLayout` stretch.
- ✅ `UI_qt/styles/theme.py`: `Palette` (dataclass) + paletas LIGHT/DARK + `build_qss(theme)` generado desde `Spacing`/`Typography`. `UI_qt/styles/__init__.py` exporta.
- ✅ Sombras de card vía `QGraphicsDropShadowEffect` (`card_shadow()`), QSS no tiene box-shadow.
- ✅ Toggle de tema light/dark en vivo (dual mode validado en la app real).
- ✅ Cableada al AppState v2. Resize sigue fluido.
- ✅ Bugs resueltos: bleed de `background-color` en `QWidget` base (labels con rectángulo feo) y orden del bootstrap de `sys.path`. Ver `docs/ui/troubleshooting-qt.md`.
- Paneles internos = placeholders (se completan en Fases 3-4).

### Fase 3 — Componentes de formulario ✅ COMPLETADA (2026-06-11)
- ✅ `UI_qt/widgets/qt_labeled_combo.py`: `QComboBox` etiquetado, sync bidireccional con ObservableVar. Reemplaza `CTkLabeledComboBox`+`CTkCustomDropdown` (510 líneas).
- ✅ `UI_qt/widgets/qt_date_edit.py`: `QtDateField` (QDateEdit calendario+escritura manual, validación de fecha intrínseca, fecha real por defecto, resaltado del día seleccionado vía QTextCharFormat).
- ✅ `UI_qt/widgets/qt_form_reserva.py`: hotel + edificio dinámico + habitación, lógica de `_on_hotel_changed`/visibilidad portada.
- ✅ `UI_qt/widgets/qt_form_fechas.py`: fechas (validación cruzada preventiva `setMinimumDate(entrada+1)`) + huéspedes (QSpinBox) + consolidación `fecha_*_completa`.
- ✅ `UI_qt/styles/icons_gen.py`: chevrons como PNG vía QPainter (SVG en QSS no renderiza en este entorno).
- ✅ Integrado en MainWindow, cableado a ControladorHotel/Precios/Validacion reutilizados. Excel real carga y puebla.
- ✅ Bugs resueltos (ver troubleshooting-qt.md): SVG data URI invisible → PNG; día seleccionado sin resaltar → QTextCharFormat; `fecha_*_completa` sin sembrar; estado vacío de QDateEdit rompía edición.
- ⏳ `QCompleter` (autocomplete) no se portó (era del `ctk_inline_suggester` del editor de email, no del form principal). Se ve en fase de modales/email.
- 📝 Pendiente estético (no bloqueante, anotado por el usuario): pulir detalles visuales finos.

### Fase 4 — Paneles de resultado ✅ COMPLETADA (2026-06-11)
- ✅ `UI_qt/widgets/qt_precio_panel.py` (`QtPrecioPanel`): monto/rango grande + subtítulo (noches, rango, nº períodos) + **desglose por período con el tramo de la reserva** (intersección reserva∩período, spec aprobada) + banner de gaps. `QScrollArea` para muchos períodos.
- ✅ `UI_qt/widgets/qt_periodos_panel.py` (`QtPeriodosPanel`): **filas expandibles** (`QToolButton` checkable + sub-frame con el rango), agrupadas por grupo. Spec aprobada.
- ✅ Integrados en `_build_right`, cableados a `precios_actualizados` y `habitacion_unificada_changed`. Flujo real validado (hotel→edificio→habitación puebla períodos y precio).
- ⏳ `VistaResultados` (`QTextEdit` readonly) se hace en Fase 5 junto al `ResultadosModal` (es parte del modal de comparación).

### Fase 5 — Modales + Fase 6 (threading) ✅ FLUJO CENTRAL COMPLETADO (2026-06-11)

Se fusionaron Fase 5 (modal de resultados) y Fase 6 (threading) porque son inseparables.

- ✅ `UI_qt/state/event_bridge.py` (`EventBridge`): QObject que escucha el EventBus y re-emite cada evento de comparación como **Qt Signal**. Como los signals cruzan de hilo con `QueuedConnection` automático, los handlers de UI corren en el hilo de la GUI aunque el scraping emita desde otro hilo. **Thread-safe sin tocar el controlador.**
- ✅ `UI_qt/widgets/qt_vista_resultados.py` (`QtVistaResultados`): `QTextBrowser` (no QTextEdit, por links clicables nativos) que renderiza el resultado en **HTML** (tabla comparativa, colores, links).
- ✅ `UI_qt/widgets/qt_progress_panel.py` (`QtProgressPanel`): `QProgressBar` + label, mismo cálculo periodos×steps que el CTk.
- ✅ `UI_qt/views/qt_resultados_modal.py` (`QtResultadosModal`): `QDialog` no-modal, conecta a los signals del bridge filtrando por `comparison_id`, soporta **comparaciones en paralelo**. Header + progreso + vista + botón email. Guarda historial.
- ✅ MainWindow: botón Ejecutar → snapshot + `ControladorComparacion.ejecutar_comparacion_async` (reutilizado SIN cambios) → modal vía `comparison_started`. Modal de gaps con `QMessageBox.question`, validación con `QMessageBox.warning`.
- ✅ **Flujo real validado**: scraping en hilo + IA (Groq) + render de tabla, sin congelar la ventana principal.
- ✅ Bug resuelto: `UnicodeEncodeError` (`→` en prints del Core sobre consola cp1252) → `sys.stdout.reconfigure(utf-8)` en el bootstrap. Ver troubleshooting-qt.md.

**DECISIÓN DE THREADING (difiere del Patrón C planeado abajo)**: NO se reescribió el controlador con `QThread`/`ScrapingWorker`. Se dejó el `threading.Thread` + EventBus existentes intactos (fiel a "no tocar controladores") y se puso el `EventBridge` del lado UI. Mismo resultado thread-safe, menos código, cero cambios al Core. El EventBus sigue siendo pub/sub puro Python (agnóstico a Qt); el bridge vive en `UI_qt`. El Patrón C de abajo queda como referencia de diseño alternativo (no implementado).

**Modales secundarios ✅ COMPLETADOS (2026-06-14)**:
- ✅ `UI_qt/views/qt_historial_modal.py` (`QtHistorialModal`): QDialog con lista scrollable de comparaciones previas; click en fila restaura al formulario (`_on_historial_restaurar` en MainWindow) y cierra; botón limpiar.
- ✅ `UI_qt/views/qt_config_modal.py` (`QtConfigModal`): QDialog + QTabWidget (General/Email/API Keys/Scraping). Email: firma + template editable con la validación portada intacta. SIN los chips clicables ni autocomplete inline del CTk (decisión de alcance: el usuario tipea las variables; documentadas en un hint).

**Sistema de iconos ✅ (2026-06-14)**:
- ✅ `UI_qt/styles/qt_icons.py`: `QIcon` desde los PNG de Feather (`UI/assets/icons/light|dark`). Reemplaza emojis en header (Historial/Config) y cards (home/clock/trash).
- ⚠️ **SVG NO disponible en este entorno**: el plugin `qsvg` no carga (Qt del wheel pip vs plugin de conda-forge no coinciden; `QImageReader.supportedImageFormats()` no incluye 'svg'). Se descartó migrar a SVG; se usan PNG + el `icons_gen.py` (chevrons QPainter→PNG). Ver troubleshooting-qt.md.

**Fixes estéticos ✅ (2026-06-14)**:
- ✅ Fondo de modales: `QDialog`/`QTextBrowser`/`QScrollArea`/`QTabWidget`/`QSpinBox`/`QMessageBox` heredaban el fondo negro del sistema (roto en light) → reglas QSS explícitas con colores del tema.
- ✅ HTML de resultados temado: rojo de discrepancias y links adaptados (light `#CC0000`/`#0066CC`, dark `#F87171`/`#60A5FA`). `QtVistaResultados`/`QtResultadosModal` reciben `theme`.
- ✅ File dialog "Cambiar": se usa el **nativo de Windows** (sin `DontUseNativeDialog`). El fallo previo era por lanzar la app en background; lanzada normal anda. Se agregó `activateWindow()`/`raise_()` antes de abrirlo.
- ✅ Panel PERÍODOS simplificado: se quitó el chevron/disclosure (la etiqueta "Período" no aportaba); ahora cada período muestra el rango de fechas directamente bajo su grupo. (Revierte parte de la spec de Figma, decisión del usuario al verlo funcionando.)

**ESTADO: la app Qt está FUNCIONALMENTE COMPLETA.** Todos los botones operan, comparación punta a punta, dual mode, modales. Falta: pulido estético adicional (si surge), Fase 7 (empaquetado), Fase 8 (toggle + borrar CTk).

### Fase 6 (REFERENCIA — Patrón C alternativo, NO implementado)

> Nota: se implementó el patrón EventBridge (arriba) en vez de este. Se conserva como referencia.

**Decisión de arquitectura**: usar `QThread` + `QObject` worker con el controlador como adapter hacia el EventBus. Esto mantiene tres capas completamente desacopladas:

```
QThread (ScrapingWorker)   ControladorComparacion (adapter)   EventBus      UI
        │                             │                           │           │
        │  Signal Qt (progress) ──►   │                           │           │
        │                    event_bus.emit('comparison_progress') ──►        │
        │                             │                       callback() ────►│
```

**Por qué no las otras opciones**:
- Opción A (bridge en EventBus): EventBus pasaría a depender de Qt → tests headless imposibles.
- Opción B (QThread puro sin EventBus): el controlador mezcla lógica de negocio con coordinación Qt.
- Opción C (elegida): cada capa tiene un único dueño — worker sabe asyncio, EventBus sigue siendo pub/sub puro Python, controlador es el único adapter.

**Tareas concretas**:

1. Crear `UI_qt/workers/scraping_worker.py` — `ScrapingWorker(QObject)`:
   - Mueve `_ejecutar_comparacion` del controlador actual al worker.
   - Emite Signals Qt propios: `progress = Signal(dict)`, `step = Signal(dict)`, `finished = Signal(dict)`, `error = Signal(str)`.
   - Corre `asyncio` con `new_event_loop()` + `run_until_complete()` + `close()` dentro de `run()`.
   - **No importa EventBus, no importa nada de UI.** Testeable standalone.

2. Refactorizar `ControladorComparacion.ejecutar_comparacion_async()`:
   - Instancia `ScrapingWorker` + `QThread`, hace `.moveToThread()`.
   - Conecta cada Signal del worker al EventBus con lambdas:
     ```python
     self._worker.progress.connect(
         lambda d: self.event_bus.emit('comparison_progress', d)
     )
     self._worker.finished.connect(
         lambda d: self.event_bus.emit('comparison_completed', d)
     )
     ```
   - El `QueuedConnection` automático de Qt garantiza que esos lambdas corran en el main thread → los `emit()` del EventBus son siempre thread-safe sin ningún marshal manual.
   - Borrar el `import tkinter as tk` muerto (línea 5 del controlador actual).

3. Aplicar el mismo patrón a los tres eventos actuales: `comparison_progress`, `scrape_step`, `comparison_completed` (y los de error).

4. **Test headless**: instanciar `ScrapingWorker` con datos mock, conectar sus signals a asserts, correr sin `QApplication`. Verificar que el EventBus sigue funcionando sin Qt en unit tests puros.

### Fase 7 — Empaquetado
- Ajustar `crawl_compare.spec` / `build_manifest.py` para PySide6.
- **Excluir módulos Qt no usados** (QtWebEngine, QtMultimedia, Qt3D, QtCharts, QtQuick...) para no inflar el `.exe`. Sin esto pesa ~100MB+; con exclusiones agresivas baja bastante. Usar `--exclude-module` y/o `PySide6.QtWebEngineCore` fuera del bundle.
- Smoke test post-build adaptado.

### Fase 8 — Limpieza
- Una vez validada la versión Qt: borrar `interfaz_ctk.py`, componentes `ctk_*`, dependencia `customtkinter`.
- Renombrar `UI_qt/` → `UI/` (o mantener nombre).
- Actualizar `docs/` (tree-directory, componentes, troubleshooting).

---

## 4. Riesgos y trade-offs (honestos)

| Riesgo | Mitigación |
|---|---|
| **Tamaño del .exe** (PySide6 infla) | Excluir módulos Qt no usados en el .spec (Fase 7). Clasificaste empaquetado como "importa pero flexible". |
| **Threading scraping → UI** | Patrón C (worker + adapter): `ScrapingWorker` emite Signals Qt, el controlador traduce al EventBus. `QueuedConnection` automático garantiza thread-safety. EventBus queda desacoplado de Qt y testeable headless. |
| **Curva de QSS/layouts** | Es lo "medio" del esfuerzo que aceptaste. Layouts Qt son más predecibles que el grid/pack de Tk. |
| **`vista_resultados` con tags de texto** | `QTextEdit` soporta rich text/HTML; mapeo directo desde los tags actuales. |
| **Reescritura del orquestador (940 líneas)** | Es el archivo más grande pero su lógica (handlers) se reutiliza; cambia solo el armado de widgets. |
| **Tiempo total** | Es una reescritura de capa de vista, no del proyecto. Por fases, con toggle, sin romper la versión CTk en el camino. |

---

## 5. Estructura de carpetas propuesta (paralela)

```
UI_qt/                         # nueva, paralela a UI/ durante la migración
├── interfaz_qt.py             # QMainWindow (reemplaza interfaz_ctk.py)
├── state/
│   ├── observable.py          # ObservableVar (Signal de Qt con API de tk.Variable)
│   ├── app_state.py           # AppState v2 (sin Tkinter)
│   └── event_bus.py           # symlink/reuse del actual (sin cambios)
├── widgets/                   # reemplaza components/
├── views/                     # modales Qt
├── styles/
│   └── theme.qss              # QSS global (traduce colors.py/spacing.py)
└── controllers/               # symlink/reuse de UI/controllers (sin cambios)
```

Controllers y EventBus se **importan de `UI/`** (no se duplican) hasta la Fase 8.

---

## 6. Decisiones CERRADAS (confirmadas por el usuario, 2026-06-10)

1. ✅ **Arrancamos por la Fase 0** (spike + medición) como GATE antes de comprometer el resto.
2. ✅ **Tema visual: QSS propio** generado desde las constantes actuales (`colors.py`/`spacing.py`/`typography.py` = fuente única de verdad). NO qt-material. Se mantiene el look exacto.
3. ✅ **Carpeta paralela `UI_qt/`** con toggle en `main.py`. CTk se borra recién al final (Fase 8) cuando esté todo migrado y validado.
4. ✅ **`vista_resultados` → `QTextEdit`** en modo de solo lectura (`setReadOnly(True)`). Es texto plano no editable, no tabla.
5. ✅ **Primera tanda = Fase 0 sola.** Se miden los números y luego se evalúa continuar.
```

