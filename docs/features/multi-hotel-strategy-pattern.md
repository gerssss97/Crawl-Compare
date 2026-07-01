# Plan — Arquitectura Multi-Hotel: Strategy + Template Method

> **Estado:** ✅ Implementado y funcionando (2026-06-30)
> Faena comparación end-to-end verificada con DOMParser + Firefox + compositions.

## Objetivo

Extender el scraper para soportar múltiples hoteles (Alvear, Faena y futuros) con dos métodos de extracción intercambiables: **LLM** (Groq actual) y **DOM** (BeautifulSoup sin LLM). El usuario elige el parser en runtime, independientemente del hotel.

## Patrón de diseño

**Strategy (doble) + Template Method**

- `SiteConfig` (Strategy 1): encapsula todo lo específico del hotel — URL, params, selectores, timeouts, anti-bot.
- `RoomParser` (Strategy 2): encapsula cómo se extraen datos — LLM o DOM.
- `HotelScraper` (Template Method): define el flujo fijo, delega los pasos variables a las dos estrategias.

## Estructura de archivos nueva

```
ScrawlingChinese/
├── crawler.py                     # crawl_alvear(), crawl_faena(), CRAWLERS dict, make_scraper()
├── config.py                      # sin cambios (backward compat)
│
├── site_configs/
│   ├── __init__.py
│   ├── alvear.py                  # AlvearConfig (DOM selectors = None por ahora)
│   └── faena.py                   # FaenaConfig (DOM selectors del handoff)
│
├── parsers/
│   ├── __init__.py
│   ├── base.py                    # Protocol RoomParser
│   ├── llm_parser.py              # LLMParser — usa LLMExtractionStrategy de Crawl4AI
│   └── dom_parser.py              # DOMParser — BeautifulSoup sobre HTML crudo
│
└── utils/
    ├── hotel_scraper.py           # HotelScraper (Template Method)
    └── scraper_utils.py           # get_browser_config(), fechas_validas(), helpers (sin cambios)
```

## SiteConfig — campos requeridos

Cada config de hotel expone:
- `NOMBRE_HOTEL`, `BASE_URL`, `CSS_SELECTOR`, `WAIT_FOR`, `PAGE_TIMEOUT_MS`
- `DOM_NOMBRE_HAB_SEL`, `DOM_PRECIO_SEL` — para DOMParser (None si no implementado)
- `LLM_INSTRUCTION` — instrucción específica del hotel para el LLM
- `build_params(fecha_ingreso, fecha_egreso, **kwargs) -> dict`
- `get_extra_browser_args() -> list[str]`

## Flujo de ejecución

```
make_scraper("faena", parser_type="dom")
    └── HotelScraper(FaenaConfig(), DOMParser(FaenaConfig()))
            ├── config.build_params()           → dict Accor
            ├── config.get_extra_browser_args() → ["--disable-blink-features=AutomationControlled"]
            ├── parser.get_extraction_strategy()→ None (Crawl4AI devuelve HTML crudo)
            └── parser.parse(result)            → BeautifulSoup extrae nombres y precios
```

## Estado DOM selectors por hotel

| Hotel  | LLMParser | DOMParser |
|--------|-----------|-----------|
| Alvear | ✅ activo | ❌ pendiente (inspeccionar HTML) |
| Faena  | ✅ listo  | ✅ selectores en handoff |

## Orden de implementación

1. ✅ `site_configs/__init__.py` + `site_configs/alvear.py`
2. ✅ `parsers/__init__.py` + `parsers/base.py` + `parsers/llm_parser.py` + `parsers/dom_parser.py`
3. ✅ `utils/hotel_scraper.py`
4. ✅ Refactor `crawler.py`: `crawl_alvear()` usa `HotelScraper`
5. ✅ `site_configs/faena.py`
6. ✅ `crawl_faena()` en `crawler.py`
7. ✅ Actualizar skill `test-scraper`

## Implementación adicional (2026-06-30)

### Wiring al stack principal (sesión 2026-06-30)
- `build_params(**kwargs)` estandarizado en todos los `SiteConfig` — cada config extrae lo que necesita del dict común (`adultos`, `ninos`, `edades_ninos`)
- `make_scraper(hotel, parser_type=None)` usa `SiteConfig.DEFAULT_PARSER` como fallback
- `DEFAULT_PARSER = "llm"` en `AlvearConfig`, `DEFAULT_PARSER = "dom"` en `FaenaConfig` (Firefox no soporta LLMExtractionStrategy)
- Cadena completa: `controlador_comparacion` → `comparar_multiperiodo` → `dar_hotel_web` → `obtener_hotel_web` → `make_scraper(scraper_key)`
- `scraper_key` derivado en el controlador como clave corta ("faena", "alvear"), separado del `hotel_nombre` usado para lookup Excel

### Feature: edades de niños para Faena/Accor
- `AppState.edades_ninos: list[int]` + `actualizar_edades_ninos(n)` (rellena con 12 por defecto)
- `QtFormFechas`: sección dinámica de spinners (min=0, max=17, default=12) visible solo cuando hotel=Faena y ninos>0, análogo al campo `edificio` del Alvear
- `edades_ninos` baja por toda la cadena hasta `FaenaConfig.build_params` → `compositions=1-12-14`

## Fix: fuzzy matching case-sensitive (2026-06-30)

**Bug:** `encontrar_mejor_match` en `Core/comparador.py` comparaba el nombre Excel (limpiado a lowercase por `limpiar_nombre_excel`) contra los nombres web tal cual vienen del scraper (UPPERCASE en Accor). RapidFuzz es case-sensitive — `"skyline"` vs `"SKYLINE"` daba scores miserables (~0.28) para todos los candidatos, haciendo que el ganador fuera casi aleatorio.

**Síntoma observado:** con 10 habitaciones disponibles, "dbl/sgl skyline view room w/bb" matcheaba a "FAENA SUITE 2-bedroom..." (score 0.316) en vez de "SKYLINE VIEW ROOM 1 king-size bed..." (score 0.290).

**Fix:** `Core/comparador.py` — agregar `nombre_web_cmp = nombre_web.lower()` y usar esa variable en las 4 métricas. El `nombre_web` original se sigue guardando en `mejores_scores` para no perder la capitalización real.

**Nota de negocio:** cuando la ocupación es alta (ej: 1 adulto + 3 niños), Accor solo renderiza las habitaciones con capacidad suficiente. Con `compositions=1-12-14-12` solo aparece la FAENA SUITE. El matcher funciona correctamente — el problema es de disponibilidad real en el sitio, no de código.
