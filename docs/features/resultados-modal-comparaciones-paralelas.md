# Feature: ResultadosModal — Comparaciones paralelas en modales independientes

> **Estado:** ✅ Implementado. Branch: `customTkinter`. Última actualización: 2026-05-26.

Si vas a tocar el flujo de comparación (eventos, progreso, resultados) o el panel
izquierdo de la GUI, leé este doc primero.

---

## Contexto

**Problema original:** El panel izquierdo (`_crear_panel_izquierdo`) contenía dos zonas:
el formulario en un `CTkScrollableFrame` (row=0) y el área de resultados `_resultados_outer`
(row=1). Como ambas zonas sumaban más altura que la ventana, el scroll del formulario
era inevitable. Además, solo se podía ejecutar una comparación a la vez (el botón
se deshabilitaba durante el scraping).

**Solución:** Los resultados se mueven a un `CTkToplevel` autónomo (`ResultadosModal`)
que se abre al presionar "Ejecutar Comparación". El formulario queda solo en el panel
izquierdo, sin scroll. Se pueden lanzar múltiples comparaciones en paralelo — cada una
abre su propio modal independiente.

---

## Archivos involucrados

| Archivo | Rol |
|---|---|
| `Hoteles/UI/views/resultados_modal.py` | **Nuevo** — modal autónomo de resultados |
| `Hoteles/UI/controllers/controlador_comparacion.py` | Modificado — `comparison_id` en firma y eventos |
| `Hoteles/UI/interfaz_ctk.py` | Modificado — eliminado `_resultados_outer`, reescritos handlers |
| `Hoteles/UI/views/__init__.py` | Modificado — exporta `ResultadosModal` |
| `Hoteles/Tests/test_error_ui_visual.py` | Modificado — inyección con nuevo contrato |
| `docs/arquitectura/tree-directory.md` | Actualizado — entrada de `resultados_modal.py` |

---

## Diseño

### `comparison_id` — la clave de aislamiento

El núcleo del feature es el `comparison_id`: un timestamp ISO con microsegundos
(`datetime.datetime.now().isoformat(timespec='microseconds')`), generado en la GUI
en `_ejecutar_comparacion()` antes de llamar al controlador.

Este ID viaja como campo en el payload de **todos** los eventos del ciclo de comparación:

| Evento | Payload antes | Payload ahora |
|---|---|---|
| `comparison_started` | `None` | `{'comparison_id': str}` |
| `comparison_progress` | `{'periodo_actual', 'total', 'estado'}` | idem + `'comparison_id'` |
| `scrape_step` | `{'step'}` | idem + `'comparison_id'` |
| `comparison_completed` | `ResultadoComparacionMultiperiodo` (objeto) | `{'comparison_id': str, 'resultado': obj}` |
| `comparison_error` | `str` | `{'comparison_id': str, 'error': str}` |

**No cambian:** `validation_failed` y `mostrar_modal_gaps` — ocurren antes de que
exista un modal y la GUI los sigue manejando directamente.

### Filtrado en el modal

Cada `ResultadosModal` filtra los eventos por su propio `comparison_id`:

```python
def _filtrar(self, data) -> bool:
    return isinstance(data, dict) and data.get('comparison_id') == self._comparison_id
```

Todos los handlers llaman `_filtrar` y hacen `return` temprano si no coincide.
Así cada modal solo reacciona a sus propios eventos, sin importar cuántas
comparaciones corran en paralelo.

### Suscripción / desuscripción del EventBus

El modal se suscribe al crearse y se desuscribe al cerrarse, limpiando los
callbacks del EventBus para evitar memory leaks:

```python
# En __init__:
self._suscribir_eventos()
self.protocol("WM_DELETE_WINDOW", self._on_cerrar)

# En _on_cerrar:
def _on_cerrar(self):
    self._desuscribir_eventos()   # EventBus.off() para cada handler
    self.destroy()
```

### Threading — `self.after(0, ...)`

Los eventos llegan desde el background thread (asyncio). Todos los updates de UI
en el modal usan `self.after(0, callback)` para encolar en el main thread de Tkinter.
`CTkToplevel` tiene su propio método `after` que despacha correctamente.

### Flujo normal (sin gaps)

```
GUI._ejecutar_comparacion()
  → genera comparison_id y snapshot
  → guarda self._ctx_pendiente = {'id': ..., 'snapshot': ...}
  → llama controlador_comparacion.ejecutar_comparacion_async(comparison_id)

Controlador (background thread):
  → valida OK, no hay gaps
  → emite comparison_started {'comparison_id': ...}

GUI._on_comparison_started(data):
  → verifica que data['comparison_id'] == ctx['id']
  → llama _lanzar_modal_comparacion(id, snapshot)   ← crea el modal
  → limpia self._ctx_pendiente

Modal:
  → recibe comparison_progress / scrape_step → actualiza progress panel
  → recibe comparison_completed → muestra resultado, guarda historial
```

### Flujo con gaps

El controlador detecta gaps **antes** de emitir `comparison_started`, así que el
modal todavía no existe cuando llega `mostrar_modal_gaps`. El modal se crea solo
si el usuario confirma:

```
GUI._on_mostrar_modal_gaps(data):
  → captura self._ctx_pendiente (snapshot del intento que disparó el gap)
  → abre CtkModalAdvertenciaGaps

Usuario confirma:
  → GUI._lanzar_modal_comparacion(ctx['id'], ctx['snapshot'])   ← crea el modal
  → GUI.controlador_comparacion.ejecutar_comparacion_async(ctx['id'])  ← relanza con mismo ID

Controlador (segunda ejecución):
  → gap_confirmado=True → pasa el check
  → emite comparison_started → el modal ya existe y lo recibe
```

### Posicionamiento escalonado

Cada modal nuevo se desplaza 28px en X e Y respecto al anterior, usando el
contador `len(self._modales_comparacion)` como `offset` en el constructor:

```python
desp = offset * 28
x = px + (pw - w) // 2 + desp
y = py + (ph - h) // 2 + desp
```

### Botón "Enviar Email" — `_FakeState`

`ModalEmail` espera un `AppState` completo. Para no modificarlo, `ResultadosModal`
construye un objeto fake que satisface solo los campos que `ModalEmail` accede:

```python
class _FakeState:
    def __init__(self, snapshot, resultado):
        self.hotel = _FakeVar(snapshot.get('hotel', ''))
        self.resultado_multiperiodo = resultado
        self.periodos_precio = []
```

---

## Layout del modal

```
┌──────────────────────────────────────────────────┐
│  Hotel Caribe — Edificio A                       │  row=0: header con snapshot
│  Suite Presidencial                              │
│  15/01 → 20/01  •  2 adultos, 1 niño            │
├──────────────────────────────────────────────────┤
│  [████████░░░░░░░]  Periodo 2/3 - Extrayendo...  │  row=1: CTkProgressPanel
├──────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────┐  │
│  │  (VistaResultados — tabla comparativa)     │  │  row=2: expande (weight=1)
│  └────────────────────────────────────────────┘  │
│                        [ Enviar Email ]           │  row=3: aparece si hay discrepancias
└──────────────────────────────────────────────────┘
  780×560, resizable, minsize(600, 400)
  Sin transient / sin grab_set — no bloqueante
```

---

## Qué se eliminó de `interfaz_ctk.py`

- `self._resultados_outer` y todo su contenido (progress panel, título, caja de resultados, `VistaResultados`)
- `self.resultado` (alias del `tk.Text` interno)
- `self._btn_email`
- `self._total_periodos_progreso`
- Handlers: `_on_comparison_progress`, `_on_scrape_step`, `_on_comparison_completed`, `_on_comparison_error`
- Métodos: `_mostrar_email_btn`, `_abrir_ventana_email`
- Imports: `tk`, `CTkProgressPanel`, `VistaResultados`, `MailtoSender`, `generar_texto_email_multiperiodo`
- `_panel_izq_outer.grid_rowconfigure(1, weight=0)` (el outer ahora tiene una sola fila)

---

## Testing

**Test visual:** `python -m Tests.test_error_ui_visual` (ejecutar desde `Hoteles/`)

Crea un `ResultadosModal` directamente e inyecta un resultado simulado vía `event_bus.emit`,
usando el nuevo contrato de payload `{'comparison_id': ..., 'resultado': ...}`.

**Verificación manual:**
1. Abrir la app, confirmar que el panel izquierdo no tiene scroll ni área de resultados
2. Completar formulario → "Ejecutar" → modal se abre con mini resumen + barra de progreso
3. "Ejecutar" de nuevo mientras corre la primera → segundo modal independiente
4. Cada modal muestra su propio resultado sin mezclarlos
5. Cerrar modal → no quedan callbacks en el EventBus (activar debug mode)
