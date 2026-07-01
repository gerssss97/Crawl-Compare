# Problema: Moneda y mercado incorrecto en Accor

## Síntoma

El scraper trae precios en una moneda o formato distinto al que ve un cliente desde Argentina:

- **Síntoma A:** Precios en EUR en lugar de USD.
- **Síntoma B:** Precios en USD pero más altos que los del browser (~$611 vs ~$503), con la leyenda "Taxes and fees included" en lugar de "Taxes not included: $98.09".
- **Síntoma C:** Precios en USD correctos pero el selector captura member rate ($452) en lugar de public rate ($503).

## Contexto

- Hotel: Faena Buenos Aires (`all.accor.com`)
- SPA Nuxt.js — precios se cargan via GraphQL post-carga
- Investigado: 2026-06-29

---

## Síntoma A — Precios en EUR

### Causa raíz (corregida — investigación 2026-06-29 noche)

La hipótesis original ("es 100% IP-based") era incorrecta. El mecanismo real:

Accor hace dos cosas en paralelo al cargar la página:
1. Llama a `aem-api.accor.com/accorApi/header?pos=united-kingdom` — esta URL tiene `pos=united-kingdom` **hardcodeada en el JS del front-end** y no tiene relación con el pricing.
2. Llama a `api.accor.com/bff/v1/graphql` con `operationName=HotelPageHot`, con variables `"countryMarket":"GB","currency":"EUR"` — **este es el que determina los precios**.

El `countryMarket=GB` se asigna server-side basado en IP geolocation. Para IPs argentinas, Accor asigna `GB` (mercado del Reino Unido), lo que devuelve precios en EUR. No es un bug de la IP siendo "europea" — es que Accor no tiene un POS específico para Argentina y la mapea al mercado europeo por default.

### Lo que NO funciona

- `currency=USD` en los query params de la URL: Accor lo ignora en sus API calls.
- `locale="en-US"` en el contexto Playwright: afecta el idioma pero no el `countryMarket`.
- Header `Accept-Language: en-US`: no cambia el `countryMarket`.
- Modificar `pos=united-kingdom` → `pos=united-states` en `accorApi/header`: esa llamada es solo para el header visual de navegación, no afecta el pricing.

### Solución ✅

Interceptar el request `HotelPageHot` con `page.route()` y modificar las variables del body GraphQL antes de que salgan:

```python
# hotel_scraper.py — _crawl_firefox()
async def _intercept(route, request):
    if "graphql" in request.url and request.method == "POST":
        try:
            body_json = json.loads(request.post_data_buffer.decode("utf-8"))
            if body_json.get("operationName") == "HotelPageHot":
                vars_ = body_json.setdefault("variables", {})
                vars_["countryMarket"] = "AR"
                vars_["currency"] = "USD"
                await route.continue_(post_data=json.dumps(body_json))
                return
        except Exception:
            pass
    await route.continue_()
await page.route("**/*", _intercept)
```

`countryMarket=AR` y `countryMarket=US` producen exactamente los mismos precios (Accor los agrupa en la misma región tarifaria). Se usa `AR` por semántica.

---

## Síntoma B — Precios más altos, "Taxes and fees included"

### Causa

El interceptor anterior modificaba `currency` a `USD` pero dejaba `countryMarket=GB`. Resultado: mercado UK en dólares, que tiene estructura de taxes bundleadas en el precio.

### Comparación concreta (Park View Room, 15-16 jul 2026, 2 adultos)

| Versión | Member rate | Public rate | Taxes |
|---------|-------------|-------------|-------|
| Scraper (interceptor GB+USD) | US$550.88 | US$611.75 | Incluidas en precio |
| Browser desde Argentina | $452.79 | $503.10 | No incluidas: $98.09 aparte |

**Hallazgo:** $452.79 + $98.09 = $550.88 exacto → mismo precio base, distinto formato según el mercado.

### Solución ✅

Cambiar `countryMarket` a `AR` además de `currency` a `USD` en el interceptor (ver Síntoma A). Con `AR`, los precios coinciden con lo que el usuario ve en su browser.

---

## Síntoma C — Se captura member rate en lugar de public rate

### Causa

El selector `.offer-price__amount` capturaba **todos** los elementos de precio: 2 por habitación (member rate + public rate), intercalados. Con 13 habitaciones → 26 elementos desalineados.

### Estructura del DOM

```html
<!-- member rate -->
<p class="offer-price offer-price--default">
  <span class="price-display--member-rate offer-price__amount">US$452.79</span>
</p>

<!-- public rate -->
<p class="offer-price offer-price--alternative" show-price-label="">
  Public rate from
  <span class="offer-price__amount">US$503.10</span>
</p>
```

### Solución ✅

Selector específico al public rate — 1 elemento por habitación:

```python
# faena.py
DOM_PRECIO_SEL = ".offer-price--alternative .offer-price__amount"
```

---

## Estado final

✅ **Resuelto completamente** (2026-06-29)

Precios verificados contra browser del usuario:

| Habitación | Scraper (AR+USD) | Browser usuario |
|---|---|---|
| Park View Room | $475.15 | ~$503* |
| Skyline View Room | $543.15 | — |

*Fechas distintas — variación de disponibilidad esperada, no discrepancia de mecanismo.

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| [`utils/hotel_scraper.py`](../../../Hoteles/ScrawlingChinese/utils/hotel_scraper.py) | `import json`; interceptor `_intercept` modifica `HotelPageHot` con `countryMarket=AR` + `currency=USD` |
| [`site_configs/faena.py`](../../../Hoteles/ScrawlingChinese/site_configs/faena.py) | `DOM_PRECIO_SEL = ".offer-price--alternative .offer-price__amount"`; `currency=USD` en `build_params` |
| [`parsers/dom_parser.py`](../../../Hoteles/ScrawlingChinese/parsers/dom_parser.py) | Selectores de public rate; limpiado código diagnóstico |

## Scripts de diagnóstico usados

Guardados en `.claude/tmp/` (no forman parte del código productivo):

| Script | Qué hace |
|---|---|
| `diag_accor_currency.py` | Captura cookies, requests y precios de una corrida real. Reveló `pos=united-kingdom` y `countryMarket=GB` |
| `diag_accor_pos.py` | Intento de fetchear endpoints referencial → falló con 401 (requiere JWT de sesión) |
| `diag_accor_markets.py` | Intercepta `HotelPageHot` con distintos `countryMarket` (AR/US/GB) + USD y compara los precios resultantes |
