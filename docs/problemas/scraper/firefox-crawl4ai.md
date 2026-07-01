# Problema: Firefox roto en Crawl4AI 0.4.x

## Síntoma

Al intentar usar Firefox como browser en Crawl4AI 0.4.x, el browser abre `http://0,0/` en lugar de la URL solicitada y falla inmediatamente. No se carga ninguna página.

```
Error: Navigation failed: net::ERR_NAME_NOT_RESOLVED http://0,0/
```

## Contexto

- Descubierto al intentar resolver el TLS fingerprinting de `api.accor.com` (ver [antibot-tls.md](antibot-tls.md))
- Versión afectada: Crawl4AI 0.4.x
- Detectado: 2026-06-29

## Causa raíz

`_build_browser_args()` en `crawl4ai/async_crawler_strategy.py:388` hardcodea más de 15 flags específicos de Chromium y los pasa a **todos** los browsers sin distinción. Uno de esos flags es `--window-position=0,0`.

Firefox interpreta `--window-position=0,0` como una URL → intenta navegar a `http://0,0/`.

El bug está en Crawl4AI, no en Playwright ni en Firefox. No hay workaround limpio dentro de Crawl4AI sin parchear la librería.

## Solución implementada

**Bypass completo de Crawl4AI para el path Firefox.** `HotelScraper._crawl_firefox()` usa Playwright directamente, sin pasar por Crawl4AI en absoluto.

```python
async with async_playwright() as p:
    browser = await p.firefox.launch(headless=headless)
    ...
```

Crawl4AI sigue usándose para el path Chromium (`_crawl_chromium()`), que no tiene este problema.

## Estado

✅ Resuelto. El path Firefox usa Playwright directo.

## Nota para el futuro

Si Crawl4AI lanza una versión que corrija el bug de args multi-browser, se podría eliminar `_crawl_firefox()` y unificar ambos paths. Verificar el changelog de Crawl4AI antes de migrar.

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| [`utils/hotel_scraper.py`](../../../Hoteles/ScrawlingChinese/utils/hotel_scraper.py) | `_crawl_firefox()` usa `async_playwright` directamente, sin `AsyncWebCrawler` |
