# Plan — Taxes Faena + Desacople de Extracción de Precio Web

> Estado: PLAN CERRADO — listo para implementar  
> Contexto: `docs/handoffs/HANDOFF-scraper-faena.md`

---

## Objetivo

1. Que el scraper del **Faena** extraiga la tarifa base ($475.15) + los impuestos ($92.80) del DOM, y compare contra Excel usando el **total** ($567.95).
2. Desacoplar la lógica de "cuál precio usar" del comparador genérico, dejando cada hotel responsable de calcular su precio comparable.

---

## Problema de diseño actual

`obtener_mejor_match_con_breakfast` en `Core/comparador.py` mezcla dos responsabilidades:

```
1. Fuzzy match  →  "qué habitación web corresponde a esta Excel"   (universal)
2. Breakfast filter  →  "qué combo de esa habitación usar"          (Alvear-only)
```

Y el comparador multiperiodo extrae el precio final así:
```python
precio_web = habitacion_web_matcheada.combos[0].precio   # hard-coded, sin taxes
```

Esto asume que TODOS los hoteles tienen combos y que el precio es solo `combo.precio`.  
Para el Faena ambas asunciones son falsas: tiene un solo combo sin titulo de breakfast, y el precio comparable es `combo.precio + impuestos`.

---

## Diseño propuesto — Strategy en SiteConfig

### Principio

Cada `SiteConfig` implementa el método `extraer_precio_web(hab_web, nombre_excel) -> float`.  
El comparador NO sabe nada de breakfast ni de taxes — solo llama al método.

```python
# FaenaConfig
def extraer_precio_web(self, hab_web: HabitacionWeb, nombre_excel: str) -> float:
    return hab_web.precio_total()              # combo[0].precio + impuestos

# AlvearConfig
def extraer_precio_web(self, hab_web: HabitacionWeb, nombre_excel: str) -> float:
    hab = aplicar_filtro_breakfast(hab_web, nombre_excel)
    return hab.precio_total()                  # combo filtrado, sin taxes (impuestos=None)
```

`precio_total()` es un método de `HabitacionWeb` que devuelve `combos[0].precio + (impuestos or 0.0)`.

### Flujo comparador (post-cambio)

```
1. Fuzzy match      →  obtener_mejor_match(nombre_excel, habitaciones_web)
                        [universal, sin lógica de breakfast]
2. Precio web       →  config.extraer_precio_web(hab_matcheada, nombre_excel)
                        [hotel-specific]
3. Comparar         →  abs(precio_excel - precio_web)
```

---

## Archivos a modificar (orden de implementación)

### 1. `Hoteles/Models/hotelWeb.py`

- Agregar `impuestos: Optional[float] = None` a `HabitacionWeb`.
- Agregar método `precio_total(self, combo_idx: int = 0) -> float`:
  ```python
  def precio_total(self, combo_idx: int = 0) -> float:
      base = self.combos[combo_idx].precio if self.combos else 0.0
      return base + (self.impuestos or 0.0)
  ```
- Actualizar funciones de display para mostrar desglose cuando `impuestos is not None`.

### 2. `Hoteles/ScrawlingChinese/site_configs/faena.py`

- Agregar `DOM_TAXES_SEL = ".stay-details__formatted-tax-type"`.
- Agregar método `extraer_precio_web`:
  ```python
  def extraer_precio_web(self, hab_web, nombre_excel: str) -> float:
      return hab_web.precio_total()
  ```

### 3. `Hoteles/ScrawlingChinese/site_configs/alvear.py`

- Agregar método `extraer_precio_web` (mueve la lógica de breakfast filtering desde `comparador.py` al config):
  ```python
  def extraer_precio_web(self, hab_web, nombre_excel: str) -> float:
      from Core.comparador import aplicar_filtro_breakfast
      hab = aplicar_filtro_breakfast(hab_web, nombre_excel)
      return hab.precio_total()
  ```

### 4. `Hoteles/ScrawlingChinese/parsers/dom_parser.py`

Extracción **obligatoria** de taxes si `DOM_TAXES_SEL` está definido en el config:
- Si `len(taxes_raw) != len(nombres)` → `raise ValueError` → el scraper reintenta.
- Si no hay `DOM_TAXES_SEL` (Alvear) → `impuestos = None` para todas las habitaciones.

```python
taxes_sel = getattr(self._config, "DOM_TAXES_SEL", None)
taxes_raw = []
if taxes_sel:
    taxes_raw = [el.get_text(strip=True) for el in soup.select(taxes_sel)]
    if len(taxes_raw) != len(nombres):
        raise ValueError(
            f"[DOMParser] Mismatch taxes vs habitaciones: "
            f"{len(taxes_raw)} taxes vs {len(nombres)} habitaciones"
        )
```

### 5. `Hoteles/Core/comparador.py`

- Renombrar `obtener_mejor_match_con_breakfast` → `obtener_mejor_match`.
- **Eliminar** la lógica de breakfast de esta función — solo hace fuzzy match y devuelve la `HabitacionWeb` completa (sin filtrar combos).
- `aplicar_filtro_breakfast` se mueve aquí (actualmente en `comparador_multiperiodo.py`) y queda disponible para que `AlvearConfig.extraer_precio_web` la importe.
- `contiene_breakfast` y las demás utilidades de fuzzy quedan en este archivo.

```python
# Nuevo nombre, sin breakfast logic:
def obtener_mejor_match(nombre_excel: str, habitaciones_web: list) -> tuple[HabitacionWeb, str]:
    nombres_web = [h.nombre for h in habitaciones_web]
    mejor_nombre, _ = encontrar_mejor_match(nombre_excel, nombres_web)
    for hab in habitaciones_web:
        if hab.nombre == mejor_nombre:
            return hab, "Match encontrado"
    return None, "No se encontró match"
```

### 6. `Hoteles/Core/comparador_multiperiodo.py`

- Agregar `site_config` como parámetro de `comparar_multiperiodo`.
- Reemplazar `obtener_mejor_match_con_breakfast(...)` → `obtener_mejor_match(...)`.
- Reemplazar el bloque de precio y filtro de breakfast por una sola línea:
  ```python
  # Antes:
  habitacion_web_matcheada, mensaje = obtener_mejor_match_con_breakfast(...)
  ...
  habitacion_web_matcheada = aplicar_filtro_breakfast(habitacion_actual, nombre_excel)
  precio_web = habitacion_web_matcheada.combos[0].precio

  # Después:
  habitacion_web_matcheada, mensaje = obtener_mejor_match(...)
  ...
  precio_web = site_config.extraer_precio_web(habitacion_web_matcheada, nombre_excel)
  ```

### 7. `Hoteles/UI_qt/controllers/controlador_comparacion.py` (call site)

Resuelve el `site_config` por inclusión de nombre antes de llamar a `comparar_multiperiodo`.
La clave del hotel (`"alvear"`, `"faena"`) siempre está contenida en el nombre del Excel (`"alvear (a)"`, `"faena buenos aires (a)"`):

```python
from ScrawlingChinese.crawler import _SITE_CONFIGS

hotel_nombre_raw = self.estado_app.hotel.get().lower()
site_config = next(
    (cfg() for clave, cfg in _SITE_CONFIGS.items() if clave in hotel_nombre_raw),
    None
)

resultado = await comparar_multiperiodo(
    ...,
    site_config=site_config,
)
```

- Limpia también los **3 imports muertos** de líneas 7-9: `comparar_habitaciones`, `dar_habitacion_web`, `dar_mensaje`.

### 8. `Hoteles/Core/controller.py` — código muerto, no tocar

`comparar_habitaciones`, `dar_habitacion_web` y `dar_mensaje` son **código muerto**: definidas pero nunca llamadas en ningún punto del codebase (verificado con grep). No se modifican ahora. Candidatos a eliminar en una sesión de limpieza posterior.

### 9. `.claude/skills/scripts/test_scraper.py`  <!-- ahora paso 8 en el orden real -->

- Output con desglose base/taxes/total cuando `hab.impuestos is not None`.

---

## Qué NO cambia

- El fuzzy matching (`encontrar_mejor_match`, `limpiar_nombre_excel`) — es universal y queda intacto.
- `contiene_breakfast` — queda en `comparador.py`, lo usa `AlvearConfig.extraer_precio_web`.
- `ResultadoPeriodo.precio_web` — sigue siendo un `float`, ahora representa el total (base+taxes).
- Tests visuales (`test_resultado_qt_visual.py`) — construyen `HabitacionWeb` sin `impuestos`, Pydantic usa default `None`, no explotan.

---

## Verificación Alvear — cero regresión

| Escenario | Antes | Después |
|-----------|-------|---------|
| Alvear + LLMParser | `combos[0].precio` (sin taxes) | `AlvearConfig.extraer_precio_web` → `aplicar_filtro_breakfast` → `precio_total()` = `combo.precio + 0.0` |
| Alvear + DOMParser | `NotImplementedError` en línea 20 | Igual, taxes_sel no se evalúa |
| Faena + DOMParser | `combos[0].precio` (sin taxes) | `FaenaConfig.extraer_precio_web` → `precio_total()` = base + taxes |
| Faena + LLMParser | `NotImplementedError` en `hotel_scraper.py` | Igual, no cambia |

---

## Decisiones tomadas (pendientes cerrados)

| # | Pendiente | Decisión |
|---|-----------|----------|
| 1 | ¿Cómo llega `site_config` a `comparar_multiperiodo`? | Se resuelve en `controlador_comparacion.py` por inclusión de nombre (`"faena" in "faena (a)"`). El comparador recibe el objeto ya instanciado. |
| 2 | ¿`aplicar_filtro_breakfast` se mueve a `comparador.py`? | Sí. Queda junto a `contiene_breakfast` y demás utilidades de matching. |
| 3 | ¿Otros importers de `obtener_mejor_match_con_breakfast`? | Solo `gestor_datos.py` (flujo legacy), pero ese flujo es **código muerto** — `comparar_habitaciones`, `dar_habitacion_web` y `dar_mensaje` nunca se llaman. Renombrar sin alias; limpiar imports muertos de `controlador_comparacion.py`. `gestor_datos.py` y `controller.py` legacy se dejan como están (no rompen nada). |
