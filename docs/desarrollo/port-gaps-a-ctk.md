# Port: Modal de Gaps a CustomTkinter

Registro del traspaso de la funcionalidad de detección y advertencia de gaps desde la rama `main` (Tkinter) a la rama `customTkinter`.

**Fecha:** 2026-03-17
**Estado:** Implementado, pendiente de prueba manual completa.

---

## Qué hace esta funcionalidad

Cuando el usuario ingresa un rango de fechas que **no tiene cobertura total** en el Excel (es decir, hay fechas sin periodo definido), el sistema:

1. **Detecta los gaps** (rangos sin cobertura) al calcular los precios.
2. **Muestra un banner amarillo** en el panel de precios indicando qué rangos no tienen cobertura.
3. **Bloquea la comparación** si el usuario no confirmó los gaps → muestra un modal CTk con el detalle.
4. Si el usuario confirma → ejecuta la comparación normalmente (solo sobre los periodos con cobertura).
5. Si cancela → no ejecuta nada.

---

## Archivos creados

### `Hoteles/Core/modelo_gaps.py` *(nuevo)*
Modelos de datos para representar gaps. Portado directamente de `main`.

- `Gap(fecha_inicio, fecha_fin)` — dataclass que representa un rango sin cobertura.
  - `get_dias()` → cantidad de días del gap
  - `formato_rango()` → string `"DD/MM/AAAA - DD/MM/AAAA"`
- `GapAnalysis` — resultado del análisis completo de cobertura.
  - `.periodos_aplicables` — periodos que sí tienen cobertura
  - `.gaps` — lista de `Gap`
  - `.tiene_gaps` — bool
  - `.get_gap_description()` → string legible para mostrar en UI

### `Hoteles/UI/components/ctk_modal_advertencia_gaps.py` *(nuevo)*
Modal CTk de advertencia. Reescritura completa del `modal_advertencia_gaps.py` de `main` (que usaba `tk.Toplevel`) usando `ctk.CTkToplevel`.

- Muestra header amarillo con el aviso
- Textbox con la descripción de gaps (read-only)
- Botones: "Continuar de Todas Formas" (azul) y "Cancelar" (gris)
- Bind `<Escape>` para cancelar
- Se centra automáticamente sobre la ventana padre
- Recibe un `callback(bool)` → `True` si el usuario confirmó, `False` si canceló

---

## Archivos modificados

### `Hoteles/Core/servicio_habitaciones.py`
Se agregaron dos funciones nuevas al final del archivo (portadas de `main`):

- `detectar_gaps(fecha_entrada, fecha_salida, periodos_aplicables) → List[Gap]`
  - Detecta brechas de cobertura entre el rango pedido y los periodos disponibles
  - Casos cubiertos: gap antes del primer periodo, gaps entre periodos, gap después del último
  - Si no hay periodos en absoluto → todo el rango es un gap

- `analizar_cobertura(fecha_entrada, fecha_salida, hotel) → GapAnalysis`
  - Función unificada que combina `inferir_periodos_desde_fechas` + `detectar_gaps`
  - Es la que usan los controladores

También se agregó el import:
```python
from Core.modelo_gaps import Gap, GapAnalysis
from datetime import date, timedelta  # timedelta era nuevo
```

### `Hoteles/UI/state/app_state.py`
Se agregaron dos atributos nuevos al `__init__` y al `reset_all`:

```python
self.gap_analysis_actual = None   # GapAnalysis | None — análisis del rango actual
self.gap_confirmado = False       # bool — True si usuario confirmó continuar con gaps
```

### `Hoteles/UI/controllers/controlador_precios.py`
Cambio central: reemplazar `inferir_periodos_desde_fechas` por `analizar_cobertura`.

En `_calcular_y_mostrar_precios`:
- Ahora llama a `analizar_cobertura(...)` y guarda el resultado en `estado_app.gap_analysis_actual`
- Resetea `gap_confirmado = False` cada vez que se recalculan precios (cambio de fechas)
- Si no hay periodos aplicables → emite `precios_actualizados` con `gap_analysis` incluido
- Si hay gaps → emite el evento `gaps_detected` (por ahora la UI no hace nada específico con esto, el panel ya muestra el banner)
- El evento `precios_actualizados` ahora incluye `gap_analysis` en el payload

### `Hoteles/UI/controllers/controlador_comparacion.py`
En `_ejecutar_comparacion`, antes de proceder:

```python
gap_analysis = getattr(self.estado_app, 'gap_analysis_actual', None)
gap_confirmado = getattr(self.estado_app, 'gap_confirmado', False)

if gap_analysis and gap_analysis.tiene_gaps and not gap_confirmado:
    self.event_bus.emit('mostrar_modal_gaps', {'gap_analysis': gap_analysis})
    return  # pausa — espera respuesta del usuario
```

Al terminar la comparación exitosamente, resetea `gap_confirmado = False` para la próxima vez.

### `Hoteles/UI/components/ctk_precio_panel.py`
`mostrar_precios_multiples` ahora acepta `gap_analysis=None` como parámetro opcional:

- Si `gap_analysis.tiene_gaps`, llama a `_mostrar_advertencia_gaps(gap_analysis)` antes de mostrar los items de precio
- Nuevo método `_mostrar_advertencia_gaps(gap_analysis)`: renderiza un banner amarillo (`#FFF3CD`) con el detalle de los gaps

### `Hoteles/UI/interfaz_ctk.py`
Se suscribieron dos eventos nuevos en `_configurar_event_listeners`:

```python
self.event_bus.on("gaps_detected", self._on_gaps_detected)
self.event_bus.on("mostrar_modal_gaps", self._on_mostrar_modal_gaps)
```

Handlers agregados:
- `_on_gaps_detected` → por ahora es `pass` (el banner ya se muestra desde el panel)
- `_on_mostrar_modal_gaps` → instancia `CtkModalAdvertenciaGaps` con un callback:
  - Si confirma: `gap_confirmado = True` y relanza `ejecutar_comparacion_async()`
  - Si cancela: `gap_confirmado = False` y no hace nada más

Se usa `self.root.after(0, lambda: ...)` para crear el modal desde el hilo principal (la comparación corre en un thread separado).

`_on_precios_actualizados` también fue actualizado para extraer `gap_analysis` del payload y pasarlo a `mostrar_precios_multiples`.

---

## Flujo completo

```
Usuario cambia fechas
  → ControladorPrecios._calcular_y_mostrar_precios()
    → analizar_cobertura() → GapAnalysis
    → guarda en estado_app.gap_analysis_actual
    → resetea gap_confirmado = False
    → si tiene_gaps → emit('gaps_detected')
    → emit('precios_actualizados', {precios, gap_analysis})
      → interfaz_ctk._on_precios_actualizados()
        → precio_panel.mostrar_precios_multiples(precios, gap_analysis)
          → si tiene_gaps → muestra banner amarillo en el panel

Usuario clickea "Ejecutar Comparación"
  → ControladorComparacion._ejecutar_comparacion()
    → si tiene_gaps y NO gap_confirmado
        → emit('mostrar_modal_gaps')
          → interfaz_ctk._on_mostrar_modal_gaps()
            → CtkModalAdvertenciaGaps(root, gap_analysis, callback)
              → Usuario confirma → gap_confirmado = True → ejecutar_comparacion_async()
              → Usuario cancela → nada
    → si sin gaps O ya confirmado → procede normalmente
    → al terminar → gap_confirmado = False
```

---

## Pendiente de verificar manualmente

- [ ] Banner amarillo se ve bien en ambos modos (light/dark) de CTk
- [ ] Modal aparece correctamente centrado
- [ ] Confirmar → comparación se ejecuta normalmente
- [ ] Cancelar → no lanza comparación, UI queda en estado limpio
- [ ] Cambiar fechas luego de cancelar → `gap_confirmado` se resetea correctamente (sí, se hace en `_calcular_y_mostrar_precios`)
- [ ] Caso sin gaps → flujo normal sin cambios visibles
- [ ] Caso sin periodos en absoluto → `sin_periodos` con `gap_analysis` en payload (no muestra banner, solo el mensaje de error)
