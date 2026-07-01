import asyncio
import json
import time
from datetime import datetime
from typing import Callable, Optional
from urllib.parse import urlencode

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig
from Models.hotelWeb import HotelWeb
from debug_config import DEBUG_SCRAPING_PIPELINE
from .scraper_utils import get_browser_config


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


class _FirefoxResult:
    """Mock result para el path Firefox-directo. DOMParser solo necesita success + html."""
    def __init__(self, html: str, final_url: str = ""):
        self.success = True
        self.html = html
        self.final_url = final_url  # URL real después de redirects
        self.extracted_content = None  # LLMParser no soportado en path Firefox


class HotelScraper:
    """
    Template Method: define el flujo fijo de scraping.
    Las estrategias SiteConfig y RoomParser determinan qué hotel y cómo parsear.
    Si el SiteConfig define BROWSER_TYPE="firefox", usa Playwright directo
    (Crawl4AI 0.4.x tiene Firefox roto por pasar flags Chromium al launcher).
    """

    def __init__(self, config, parser):
        self._config = config
        self._parser = parser

    async def crawl(
        self,
        fecha_ingreso: str,
        fecha_egreso: str,
        on_scrape_step: Optional[Callable[[str], None]] = None,
        max_reintentos: int = 3,
        delay_entre_reintentos: int = 5,
        **kwargs,
    ) -> Optional[HotelWeb]:
        params = self._config.build_params(fecha_ingreso, fecha_egreso, **kwargs)
        url_completa = f"{self._config.BASE_URL}?{urlencode(params)}"

        print(f"[{_ts()}] Hotel: {self._config.NOMBRE_HOTEL}")
        print(f"[{_ts()}] Parser: {type(self._parser).__name__}")
        print(f"[{_ts()}] URL: {url_completa}")

        def _notify(step: str):
            if on_scrape_step:
                on_scrape_step(step)

        if getattr(self._config, "BROWSER_TYPE", "chromium") == "firefox":
            if self._parser.get_extraction_strategy() is not None:
                raise NotImplementedError(
                    f"{type(self._parser).__name__} no soportado en el path Firefox. "
                    "Usá --parser=dom para este hotel."
                )
            return await self._crawl_firefox(
                url_completa, _notify, max_reintentos, delay_entre_reintentos
            )

        return await self._crawl_chromium(
            url_completa, _notify, max_reintentos, delay_entre_reintentos
        )

    async def _crawl_firefox(
        self,
        url: str,
        notify: Callable,
        max_reintentos: int,
        delay_entre_reintentos: int,
    ) -> Optional[HotelWeb]:
        """Path Playwright-directo para sitios con TLS fingerprinting anti-Chromium."""
        from playwright.async_api import async_playwright

        headless = getattr(self._config, "HEADLESS", True)
        user_agent = getattr(self._config, "USER_AGENT", None)
        timeout_ms = self._config.PAGE_TIMEOUT_MS

        # Crawl4AI usa "css:selector" — Playwright solo necesita "selector"
        wait_for_raw = self._config.WAIT_FOR
        css_selector = wait_for_raw.removeprefix("css:") if wait_for_raw else None

        print(f"[{_ts()}] Timeout: {timeout_ms // 1000}s | wait_for: {css_selector}")
        print(f"[{_ts()}] Iniciando browser Firefox...")

        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=headless)
            try:
                ctx_kwargs = {"locale": "en-US"}
                if user_agent:
                    ctx_kwargs["user_agent"] = user_agent
                context = await browser.new_context(**ctx_kwargs)

                for intento in range(max_reintentos):
                    print(f"[{_ts()}] --- Intento {intento + 1}/{max_reintentos} ---")
                    page = await context.new_page()
                    t0 = time.time()

                    def _on_request(req):
                        if any(d in req.url for d in ["api.accor", "accor.com/api", "accorhotels"]):
                            print(f"[{_ts()}]   >> {req.method} {req.url[:120]}")

                    def _on_response(resp):
                        if any(d in resp.url for d in ["api.accor", "accor.com/api", "accorhotels"]):
                            print(f"[{_ts()}]   << {resp.status} {resp.url[:120]}")

                    page.on("request", _on_request)
                    page.on("response", _on_response)

                    try:
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

                        notify("FETCH")
                        print(f"[{_ts()}] Navegando a la pagina...")
                        response = await page.goto(url, wait_until="networkidle")
                        status = getattr(response, "status", "?")
                        print(f"[{_ts()}] Pagina recibida (HTTP {status}).")

                        notify("SCRAPE")
                        if css_selector:
                            print(f"[{_ts()}] Esperando selector '{css_selector}'...")
                            await page.wait_for_selector(css_selector, timeout=timeout_ms)

                        # Esperamos el selector de precios directamente en el DOM.
                        # wait_for_response("affiliation-and-identification") no funciona:
                        # ese request ya ocurrió durante el networkidle de goto() y
                        # los listeners de wait_for_response solo capturan respuestas futuras.
                        precio_sel = getattr(self._config, "DOM_PRECIO_SEL", None)
                        if precio_sel:
                            try:
                                print(f"[{_ts()}] Esperando precios '{precio_sel}'...")
                                await page.wait_for_selector(precio_sel, timeout=15000)
                                print(f"[{_ts()}] Precios en DOM.")
                                await asyncio.sleep(1)
                            except Exception:
                                print(f"[{_ts()}] Selector de precios timeout — capturando HTML diagnóstico...")

                        notify("EXTRACT")
                        html = await page.content()
                        final_url = page.url
                        elapsed = time.time() - t0
                        kb = len(html) // 1024
                        print(f"[{_ts()}] HTML capturado ({kb} KB) en {elapsed:.1f}s")
                        print(f"[{_ts()}] URL final (post-redirect): {final_url}")

                        result = _FirefoxResult(html, final_url=final_url)
                        notify("COMPLETE")
                        hotel = await self._parser.parse(result, url)

                        if hotel and hotel.habitacion:
                            print(f"[{_ts()}] Parseado OK: {len(hotel.habitacion)} habitaciones")
                            await page.close()
                            return hotel

                        print(f"[{_ts()}] Parser no devolvio habitaciones. Reintentando en {delay_entre_reintentos}s...")
                        await page.close()
                        await asyncio.sleep(delay_entre_reintentos)

                    except Exception as e:
                        elapsed = time.time() - t0
                        print(f"[{_ts()}] Excepcion en intento {intento + 1} ({elapsed:.1f}s): {e}")
                        await page.close()
                        if intento < max_reintentos - 1:
                            await asyncio.sleep(delay_entre_reintentos)
                        else:
                            raise
            finally:
                await browser.close()

        raise Exception(
            f"No se obtuvieron datos despues de {max_reintentos} intentos.\nURL: {url}"
        )

    async def _crawl_chromium(
        self,
        url: str,
        notify: Callable,
        max_reintentos: int,
        delay_entre_reintentos: int,
    ) -> Optional[HotelWeb]:
        """Path Crawl4AI/Chromium para sitios sin TLS fingerprinting (ej: Alvear)."""
        print(f"[{_ts()}] Timeout: {self._config.PAGE_TIMEOUT_MS // 1000}s | wait_for: {self._config.WAIT_FOR}")

        browser_config = get_browser_config(
            extra_args=self._config.get_extra_browser_args(),
            user_agent=getattr(self._config, "USER_AGENT", None),
            headless=getattr(self._config, "HEADLESS", None),
            browser_type=getattr(self._config, "BROWSER_TYPE", "chromium"),
        )
        extraction_strategy = self._parser.get_extraction_strategy()

        _page_ref = {}

        async def _before_goto(page, context, url, **kw):
            _page_ref["page"] = page
            print(f"[{_ts()}] Navegando a la pagina...")
            notify("FETCH")
            return page

        async def _after_goto(page, context, url, response, **kw):
            status = getattr(response, "status", "?")
            print(f"[{_ts()}] Pagina recibida (HTTP {status}). Esperando selector '{self._config.WAIT_FOR}'...")

            def _on_request(req):
                if any(d in req.url for d in ["api.accor", "accor.com/api", "ahstatic", "accorhotels"]):
                    print(f"[{_ts()}]   >> {req.method} {req.url[:120]}")

            def _on_response(resp):
                if any(d in resp.url for d in ["api.accor", "accor.com/api", "ahstatic", "accorhotels"]):
                    print(f"[{_ts()}]   << {resp.status} {resp.url[:120]}")

            page.on("request", _on_request)
            page.on("response", _on_response)
            notify("SCRAPE")
            return page

        async def _before_retrieve_html(page, context, **kw):
            print(f"[{_ts()}] Selector encontrado. Capturando HTML...")
            notify("EXTRACT")
            return page

        async def _before_return_html(page, context, html, **kw):
            kb = len(html) // 1024 if html else 0
            has_container = "hotel-accommodations" in (html or "")
            has_title = "hotel-accommodations-offers__item-title" in (html or "")
            has_price = "offer-price__amount" in (html or "")
            print(f"[{_ts()}] HTML capturado ({kb} KB) | container={has_container} | item_title={has_title} | price={has_price}")
            if not has_title and html:
                print(f"[{_ts()}] HTML inicio (head):\n{html[:1200]!r}")
                for marker in ["datadome", "akamai", "perimeterx", "_dd_", "imperva", "cloudflare", "distil"]:
                    if marker.lower() in html.lower():
                        print(f"[{_ts()}] [!] Bot-detection detectado en HTML: {marker}")
            notify("COMPLETE")
            return page

        print(f"[{_ts()}] Iniciando browser Chromium...")

        async with AsyncWebCrawler(config=browser_config) as crawler:
            crawler.crawler_strategy.set_hook("before_goto", _before_goto)
            crawler.crawler_strategy.set_hook("after_goto", _after_goto)
            crawler.crawler_strategy.set_hook("before_retrieve_html", _before_retrieve_html)
            crawler.crawler_strategy.set_hook("before_return_html", _before_return_html)

            for intento in range(max_reintentos):
                print(f"[{_ts()}] --- Intento {intento + 1}/{max_reintentos} ---")
                t0 = time.time()
                try:
                    delay = getattr(self._config, "DELAY_BEFORE_RETURN_HTML", 0)
                    run_kwargs = dict(
                        scan_full_page=False,
                        cache_mode=CacheMode.BYPASS,
                        extraction_strategy=extraction_strategy,
                        css_selector=self._config.CSS_SELECTOR,
                        wait_for=self._config.WAIT_FOR,
                        wait_until="networkidle",
                        page_timeout=self._config.PAGE_TIMEOUT_MS,
                        magic=getattr(self._config, "USE_MAGIC", False),
                    )
                    if delay:
                        run_kwargs["delay_before_return_html"] = delay
                        print(f"[{_ts()}] Modo diagnostico: delay fijo {delay}s, sin wait_for")
                    result = await crawler.arun(
                        url=url,
                        config=CrawlerRunConfig(**run_kwargs),
                    )

                    elapsed = time.time() - t0
                    print(f"[{_ts()}] arun() termino en {elapsed:.1f}s | success={result.success}")

                    if not result.success:
                        print(f"[{_ts()}] Error: {result.error_message}")
                        page = _page_ref.get("page")
                        if page:
                            try:
                                html_actual = await page.content()
                                kb = len(html_actual) // 1024
                                print(f"[{_ts()}] HTML en fallo ({kb} KB): {html_actual[:800]!r}")
                            except Exception as pe:
                                print(f"[{_ts()}] No se pudo capturar HTML post-fallo: {pe}")

                    hotel = await self._parser.parse(result, url)

                    if hotel and hotel.habitacion:
                        print(f"[{_ts()}] Parseado OK: {len(hotel.habitacion)} habitaciones")
                        return hotel

                    print(f"[{_ts()}] Parser no devolvio habitaciones. Reintentando en {delay_entre_reintentos}s...")
                    await asyncio.sleep(delay_entre_reintentos)

                except Exception as e:
                    elapsed = time.time() - t0
                    print(f"[{_ts()}] Excepcion en intento {intento + 1} ({elapsed:.1f}s): {e}")
                    if intento < max_reintentos - 1:
                        await asyncio.sleep(delay_entre_reintentos)
                    else:
                        raise

        raise Exception(
            f"No se obtuvieron datos despues de {max_reintentos} intentos.\nURL: {url}"
        )
