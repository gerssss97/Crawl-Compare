# Handoff — Dispatch Faena Wiring — 2026-06-30

> Sesión: Wiring completo del dispatch multi-hotel + feature edades niños para Faena
> Tema: Scraper / Core / UI_qt

## Objetivo

Cerrar el bug [crawl-dispatch-hardcoded](../problemas/scraper/crawl-dispatch-hardcoded.md): `gestor_datos.py` siempre llamaba `crawl_alvear` sin importar qué hotel estaba seleccionado. Al mismo tiempo, extender la arquitectura para soportar múltiples hoteles de forma limpia y agregar el input de edades de niños requerido por Accor/Faena.

## Progreso actual

**Completado.** Faena funciona end-to-end desde la UI:
- Dispatch correcto por hotel via `make_scraper(scraper_key)`
- DOMParser + Firefox automático para Faena
- `compositions=1-12-14` construido correctamente desde edades ingresadas en la UI
- Resultado visible en el modal de comparación

**Pendiente:** fuzzy matching de nombres de habitaciones — el matcher no liga bien nombres en español (Excel) con inglés (web Accor). En el test se matcheó "dbl/sgl park view room w/buffet breakfast" → "DUPLEX SUITE 1 king-size bed 75m2/810sft", que es incorrecto.

## Lo que funcionó

- `build_params(**kwargs)` en todos los `SiteConfig` — cada config extrae lo que necesita del dict común; agregar un hotel nuevo es solo agregar una `SiteConfig` con su propio `build_params`
- `DEFAULT_PARSER` por config (`"llm"` en Alvear, `"dom"` en Faena) — `make_scraper(hotel, parser_type=None)` lo lee como fallback
- `scraper_key` derivado en `controlador_comparacion.py` con `next(clave for clave in _SITE_CONFIGS if clave in hotel_nombre_raw)`, separado del `hotel_nombre` que va al lookup de Excel
- Sección de edades en `QtFormFechas`: spinners dinámicos (default 12, max 17) que aparecen solo si hotel=Faena y ninos>0, análogo al campo `edificio` del Alvear

## Lo que no funcionó

- **`_es_faena()` con `normalizar_hotel_nombre(...) == "faena"`**: `normalizar_hotel_nombre` devuelve `"faena hotel buenos aires (a)"`, no la clave corta. Fix: `"faena" in self.state.hotel.get().lower()`
- **`hotel_nombre` pasado como nombre largo de Excel**: en la primera versión, `hotel_nombre = normalizar_hotel_nombre(...)` ("alvear palace hotel (a)") llegaba a `make_scraper` y tiraba `KeyError`. Fix: derivar `scraper_key` por separado
- **`parser_type="llm"` hardcodeado en `crawl_alvear`/`crawl_faena`**: al ser truthy, pisaba el `DEFAULT_PARSER`. Fix: cambiar default a `None` en ambas funciones y en `extraer_parser_type` del test_scraper
- **Same-day check-in en Accor**: Accor no renderiza el selector de precios `.offer-price--alternative .offer-price__amount` para check-in el mismo día — todos los intentos fallan por timeout. No es un bug de código; limitación del sitio

## Próximos pasos

1. ~~**Fuzzy matching para Faena**~~ ✅ Resuelto — ver continuación 2026-06-30 más abajo
2. **Bug preexistente**: `[EventBus] Error en listener de habitacion_unificada_changed: 'NoneType' object has no attribute 'precio_para_periodo'` — ocurre al resetear la selección de hotel/habitacion. No bloquea nada pero genera ruido en los logs

---

## Continuación — 2026-06-30 (Fuzzy Matching Fix)

### Objetivo

Investigar y corregir el matcher que elegía la habitación incorrecta en Faena. El handoff anterior lo dejaba como pendiente con hipótesis de "diferencia de idioma" (Excel en español, web en inglés).

### Lo que encontramos

La hipótesis de idioma era incorrecta. Accor muestra los nombres en inglés — igual que el Excel de Faena. El verdadero problema era **case sensitivity**.

Proceso de diagnóstico:
1. Habilitamos `DEBUG_SCRAPING_PIPELINE = True` y `DEBUG_FUZZY_MATCHING = True` en `debug_config.py`
2. Agregamos prints en `dom_parser.py` para ver cuántos elementos encontraba cada selector y sus valores
3. Agregamos prints en `comparador.py` mostrando el nombre Excel limpio y los 4 scores por candidato

**Hallazgo clave del log:**
```
[DOM] Selector nombres → 10 elementos
  [0] SKYLINE VIEW ROOM 1 king-size bed, 45m2/484sft
  ...
[FUZZY] Excel limpio: 'skyline view room bb'
  [SKYLINE VIEW ROOM ...] ratio=0.242 partial=0.400 → TOTAL=0.290
  [FAENA SUITE ...]      ratio=0.200 partial=0.400 → TOTAL=0.316  ← ganaba (incorrecto)
```

`limpiar_nombre_excel` pasa el nombre a lowercase. Los nombres web vienen en UPPERCASE de Accor. RapidFuzz es case-sensitive — `"skyline"` vs `"SKYLINE"` da scores bajos para todos los candidatos, el ganador queda determinado por ruido estadístico.

**Hallazgo adicional de negocio:** con `compositions=1-12-14-12` (1 adulto + 3 niños), Accor solo renderiza habitaciones con capacidad suficiente — en ese caso 1 sola (FAENA SUITE). El matcher no tiene más candidatos. No es un bug de código sino de disponibilidad real del sitio.

### Fix aplicado

`Hoteles/Core/comparador.py` — en el loop de `encontrar_mejor_match`, agregar:
```python
nombre_web_cmp = nombre_web.lower()
# usar nombre_web_cmp en las 4 métricas de RapidFuzz
# nombre_web (original) sigue siendo lo que se guarda en mejores_scores
```

### Archivos tocados en esta continuación

| Archivo | Cambio |
|---------|--------|
| `Hoteles/Core/comparador.py` | Fix case-sensitivity: `nombre_web_cmp = nombre_web.lower()` antes de las 4 métricas; prints de debug con `DEBUG_FUZZY_MATCHING` |
| `Hoteles/ScrawlingChinese/parsers/dom_parser.py` | Prints de debug (cantidad de elementos encontrados por selector, valores) guardados con `DEBUG_SCRAPING_PIPELINE` |
| `Hoteles/debug_config.py` | `DEBUG_FUZZY_MATCHING = True`, `DEBUG_SCRAPING_PIPELINE = True` (temporales para debug, dejar en True para prod según la convención del archivo) |
| `docs/features/multi-hotel-strategy-pattern.md` | Documentado el fix de case-sensitivity y la nota de negocio sobre ocupación |

## Archivos clave tocados

| Archivo | Cambio |
|---------|--------|
| `Hoteles/Core/gestor_datos.py` | `obtener_hotel_web` recibe `hotel_nombre` y `edades_ninos`; usa `make_scraper(hotel_nombre)` en lugar de `crawl_alvear` hardcodeado |
| `Hoteles/Core/controller.py` | `dar_hotel_web` propaga `hotel_nombre` y `edades_ninos` |
| `Hoteles/Core/comparador_multiperiodo.py` | `comparar_multiperiodo` recibe `hotel_nombre` y `edades_ninos`; los pasa a `dar_hotel_web`; logs de diagnóstico |
| `Hoteles/UI_qt/controllers/controlador_comparacion.py` | Deriva `scraper_key` corto para el scraper; lee `edades_ninos` del estado; logs de diagnóstico |
| `Hoteles/UI_qt/state/app_state.py` | Agrega `edades_ninos: list[int]` y `actualizar_edades_ninos(n)` |
| `Hoteles/UI_qt/widgets/qt_form_fechas.py` | Sección dinámica de spinners de edad; `_es_faena()` via `"faena" in hotel.lower()` |
| `Hoteles/ScrawlingChinese/crawler.py` | `make_scraper` con `parser_type=None` + `DEFAULT_PARSER` fallback; `crawl_alvear`/`crawl_faena` con `parser_type=None` |
| `Hoteles/ScrawlingChinese/site_configs/alvear.py` | `build_params(**kwargs)`; `DEFAULT_PARSER = "llm"` |
| `Hoteles/ScrawlingChinese/site_configs/faena.py` | `build_params(**kwargs)`; `DEFAULT_PARSER = "dom"` |
| `.claude/skills/scripts/test_scraper.py` | `extraer_parser_type` defaultea a `None` en lugar de `"llm"` |
| `docs/problemas/scraper/crawl-dispatch-hardcoded.md` | Marcado como ✅ Resuelto |
| `docs/features/multi-hotel-strategy-pattern.md` | Actualizado con estado de implementación y pendientes |
