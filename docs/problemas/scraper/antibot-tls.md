# Problema: TLS Fingerprinting en api.accor.com

## Síntoma

Al scrapear el Faena Buenos Aires (`all.accor.com`), Playwright con Chromium no recibe respuestas de `api.accor.com`. El HTML resultante tiene 84 KB sin ninguna habitación. En consola se ve:

```
<< 200  (ninguna respuesta de api.accor.com aparece)
```

El scraper devuelve 0 habitaciones después de esperar el networkidle.

## Contexto

- Hotel: Faena Buenos Aires (`all.accor.com/booking/en/accor/hotel/B8G3`)
- SPA Nuxt.js — las habitaciones llegan via API REST/GraphQL post-carga
- Detectado: 2026-06-28 / 2026-06-29

## Investigación: intentos fallidos

| Test | Resultado | Aprendizaje |
|------|-----------|-------------|
| Headless Chromium, `magic=True` (tf-playwright-stealth) | Sin responses de `api.accor.com` | Stealth JS no toca TLS |
| Headless Chromium, delay fijo 20s | HTML 84 KB sin rooms, cero responses | La API cuelga la conexión, no es timeout |
| Inspección de `<head>` del HTML | GTM + Kameleoon — sin DataDome/PerimeterX/Akamai | No es anti-bot comercial estándar |
| Headed Chromium (browser visible) | Misma página de error "Technical error" | No es detección de headless |
| Firefox via Crawl4AI 0.4.x | `http://0,0/` — Firefox roto en esta versión | Ver [firefox-crawl4ai.md](firefox-crawl4ai.md) |
| **Firefox via Playwright directo** | **`<< 200` en todas las APIs, 360 KB con rooms** | **TLS fingerprinting confirmado** |

## Causa raíz

`api.accor.com` aplica **TLS fingerprinting (JA3/JA4)**: detecta la firma del handshake TLS de Playwright's Chromium y cierra la conexión silenciosamente. Firefox tiene una firma TLS distinta → pasa sin problema.

`tf-playwright-stealth` (incluida en Crawl4AI 0.4.x como `magic=True`) parchea el fingerprinting de JavaScript del browser (navigator.webdriver, User-Agent, etc.) pero **no modifica el handshake TLS** — por eso `magic=True` no ayudó.

## Solución implementada

Firefox headless via **Playwright directo** (sin Crawl4AI). Ver [`HotelScraper._crawl_firefox()`](../../../Hoteles/ScrawlingChinese/utils/hotel_scraper.py).

En `FaenaConfig`:
```python
BROWSER_TYPE = "firefox"
```

`HotelScraper.crawl()` detecta `BROWSER_TYPE == "firefox"` y desvía a `_crawl_firefox()`, que lanza Playwright directo. El path Chromium/Crawl4AI queda intacto para otros hoteles (ej: Alvear).

## Estado

✅ Resuelto. 13 habitaciones extraídas en ~7s con Firefox headless.

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| [`site_configs/faena.py`](../../../Hoteles/ScrawlingChinese/site_configs/faena.py) | `BROWSER_TYPE="firefox"`, `HEADLESS=True`, `USER_AGENT` Firefox |
| [`utils/hotel_scraper.py`](../../../Hoteles/ScrawlingChinese/utils/hotel_scraper.py) | Split `_crawl_firefox()` + `_crawl_chromium()`, guard para LLMParser |
