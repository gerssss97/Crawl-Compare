# Handoff — 2026-06-23

> Sesión: debugging del bug click-to-open en `QtLabeledCombo` — popup se abría y se cerraba instantáneamente.

## Objetivo

Resolver el bug donde hacer click en el line edit del combo (no en la flechita) abría el dropdown y lo cerraba de inmediato. La sesión anterior ya tenía implementado el `_LineEditClickFilter` con `QTimer.singleShot(0, showPopup)`, pero no funcionaba.

---

## Progreso actual

| Feature | Estado |
|---------|--------|
| Typeahead con QCompleter (MatchContains) | ✅ Funciona |
| Tipear con dropdown nativo abierto (filtra) | ✅ Funciona |
| Esquinas redondeadas del popup | ✅ Funciona |
| Click en el line edit → abrir dropdown | ⚠️ Fix implementado, pendiente de verificar en limpio |

El fix actual usa una **ventana temporal de 20ms** (`time.monotonic()`) para suprimir los `hidePopup` espurios. No fue posible probarlo antes del handoff.

---

## Root cause — diagnosticado con certeza

Cuando `showPopup()` es llamado desde nuestro `singleShot(0)`, Qt::Popup abre una nueva ventana top-level. Windows genera mensajes de activación (`WM_ACTIVATE`, `WM_NCACTIVATE`, etc.) que Qt traduce en llamadas `hidePopup()` directas desde el event loop C++.

Estos hides son **múltiples e independientes** (4 calls espurios sobre la misma instancia en los tests), y llegan en microsegundos después de `showPopup()`.

### Detalles clave descubiertos:

- **Atributos de instancia PySide6 no sobreviven** el ciclo Python→C++→Python de `super().showPopup()`. `self._suppress_hide = True` quedaba en `False` al llegar a `hidePopup`. Confirmado con `getattr(self, '_suppress_hide', 'MISSING')` que mostraba `MISSING`.

- **Módulo-level set/dict SÍ funciona** (mismo `id()` del objeto, mismo `id()` del set). Los prints confirmaron que el set es el mismo objeto en `_open()` y en `hidePopup`.

- **`QTimer.singleShot(50, cleanup)` se dispara ANTES** de que lleguen los `hidePopup` espurios. La resolución del timer de Windows (~15.6ms) hace que un timer de 50ms se dispare a ~46ms, pero los hides pueden tardar más en procesar. Resultado: timer limpia el set, hides llegan, set vacío.

- **Contador `_suppress_hide_counts`** (2, luego 3): al bloquear N hides, aparece un nuevo hide espurio N+1. Cada hide bloqueado genera retroalimentación. Además, bloquear sin llamar `super()` deja el estado interno de Qt inconsistente con el visual → selección no cerraba el popup, scroll raro.

---

## Lo que funcionó

- **Diagnóstico sistemático**: `traceback.print_stack()` en `showPopup`/`hidePopup`, `id(self)`, `id(_suppress_until)`, contenidos del set en cada punto → confirmó que mismo objeto, mismo set, pero set vaciado antes del check.

- **`_suppress_until: dict[int, float]`** a nivel módulo con ventana de 20ms usando `time.monotonic()`:
  ```python
  # En _open():
  _suppress_until[id(self._combo)] = time.monotonic() + 0.020
  self._combo.showPopup()
  
  # En hidePopup():
  if id(self) in _suppress_until:
      if time.monotonic() < _suppress_until[id(self)]:
          return  # bloqueado
      del _suppress_until[id(self)]
  super().hidePopup()
  ```
  Ventaja: el cleanup se hace dentro de `hidePopup` mismo (sin timers externos), y la comparación temporal es immune al problema de "timer se dispara antes".

---

## Lo que no funcionó

- **`self._suppress_hide = True` (atributo de instancia PySide6)**: La transición Python→C++→Python en `super().showPopup()` resetea el `__dict__` del wrapper PySide6. El atributo era `True` al entrar a `showPopup`, `False` al llegar a `hidePopup`.

- **`_suppress_hide_ids: set[int]` con `QTimer.singleShot(50, discard)`**: El timer de cleanup disparaba ANTES que los hides espurios, dejando el set vacío. Causa: resolución del timer Windows (~15.6ms) vs. demora del event loop procesando mensajes WM_ACTIVATE.

- **`_suppress_hide_counts: dict[int, int]` con contador**: Bloquear N hides generaba un hide espurio N+1 (retroalimentación infinita). Además, bloquear sin llamar `super().hidePopup()` dejaba inconsistencia visual ≠ estado interno Qt → selección no cerraba el popup, scroll se iba solo al final.

- **`QTimer.singleShot(0, showPopup)` directo**: El popup se abría y cerraba porque los mensajes WM_ACTIVATE ya estaban en la cola y llegaban en el mismo ciclo del event loop.

---

## Estado del archivo qt_labeled_combo.py

**Ojo: el archivo tiene código de diagnóstico activo** (`import traceback`, prints con `[DIAG]`, `_show_count`, `_hide_count`, `[FILTER]` prints). Hay que limpiarlo antes de considerar el fix listo para producción.

Clases en el archivo:
- `_RoundedCombo(QComboBox)` — esquinas redondeadas + `showPopup`/`hidePopup` overrides con diagnóstico y la ventana temporal `_suppress_until`
- `_LineEditClickFilter(QObject)` — intercepta `MouseButtonPress` y llama `singleShot(0, _open)` con la ventana temporal
- `_DropdownKeyFilter(QObject)` — funciona: tipear con dropdown abierto filtra
- `QtLabeledCombo(QWidget)` — widget público, sin cambios funcionales

---

## Próximos pasos

1. **Verificar el fix de 20ms**: correr la app, hacer click en el line edit, confirmar que:
   - El popup queda abierto
   - Seleccionar una opción lo cierra
   - Escape / click afuera lo cierran
   - El scroll con mouse funciona normal

2. **Si el fix funciona**: limpiar todo el código de diagnóstico del archivo:
   - Sacar `import traceback`
   - Sacar `_show_count`, `_hide_count`, `_suppress_hide`, `getattr(_suppress_hide, 'MISSING')`
   - Sacar todos los `print([DIAG])` y `print([FILTER])`
   - Limpiar las funciones a su forma final sin diagnóstico

3. **Si el fix NO funciona** con 20ms: probar con 50ms o 100ms. Si con 100ms tampoco funciona, el problema es estructural (no es un timing issue del cleanup sino de la propia apertura del popup).

4. **Alternativa si el timing no resuelve**: Simular click en la flechita nativa desde el event filter, en lugar de llamar `showPopup()` directamente. Qt tiene guards internos al abrir desde la flechita que no aplican en llamadas externas.

---

## Archivos clave tocados

| Archivo | Cambio |
|---------|--------|
| `Hoteles/UI_qt/widgets/qt_labeled_combo.py` | Fix click-to-open con `_suppress_until` (ventana 20ms) + diagnóstico activo aún |
