import json
import os
from typing import List, Set, Tuple, Callable, Optional
from urllib.parse import urlencode
import asyncio

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    LLMExtractionStrategy,
)
from datetime import date
from Models.hotelExcel import *
from Models.hotelWeb import *
from debug_config import DEBUG_CRAWL4AI_VERBOSE, DEBUG_SCRAPING_PIPELINE, DEBUG_LLM_MARKDOWN, DEBUG_COMPARISON_PIPELINE


def get_browser_config() -> BrowserConfig:
    """
    Returns the browser configuration for the crawler.

    Returns:
        BrowserConfig: The configuration settings for the browser.
    """
    # https://docs.crawl4ai.com/core/browser-crawler-config/
    return BrowserConfig(
        browser_type="chromium",  # Type of browser to simulate
        headless=False,  # Whether to run in headless mode (no GUI)
        verbose=DEBUG_CRAWL4AI_VERBOSE,

        # ===== OPTIMIZACIONES DE RENDIMIENTO =====
        # Flags para acelerar carga de página sin perder datos
        extra_args=[
            # FLAG 1: Evita detección de bot (0-500ms ganancia)
            # Elimina navigator.webdriver=true para que el sitio no active defensas anti-bot
            # "--disable-blink-features=AutomationControlled",

            # FLAG 2: Deshabilita red en background (500-1500ms ganancia) - ACTIVADO
            # Evita telemetría, actualizaciones, crash reports
            # Reduce "ruido" de red → wait_until="networkidle" termina más rápido
            "--disable-background-networking",

            # FLAG 3: Deshabilita extensiones del navegador (200-500ms ganancia)
            # Las extensiones consumen CPU/memoria y hacen requests adicionales
            "--disable-extensions",

            # FLAG 4: Deshabilita barra de traducción (50-100ms ganancia)
            # Evita que Chrome analice el idioma y cargue recursos de traducción
            "--disable-features=TranslateUI",
        ],
    )


def get_llm_strategy() -> LLMExtractionStrategy:
    """
    Returns the configuration for the language model extraction strategy.

    Returns:
        LLMExtractionStrategy: The settings for how to extract data using LLM.
    """
    # https://docs.crawl4ai.com/api/strategies/#llmextractionstrategy

    return LLMExtractionStrategy(
        # ===== MODELO FINAL: Balance perfecto velocidad/límites =====
        # Progresión de modelos probados:
        # - gpt-oss-20b: 40-60s (demasiado lento)
        # - llama-3.1-8b-instant: 2-5s ❌ RATE LIMIT (6k tokens/min) - no soporta multi-periodo
        # - llama-3.1-70b-versatile: ❌ DEPRECADO (modelo descontinuado por Groq)
        # - llama-3.3-70b-versatile: 10-20s ✅ ÓPTIMO (30k tokens/min, modelo actual)
        #
        # Modelos activos 2026 con límites:
        # - llama-3.3-70b-versatile: 30k tokens/min ✅ (recomendado - mejor calidad)
        # - llama3-8b-8192: 30k tokens/min ✅ (alternativa más rápida, menos calidad)
        # - llama-3.1-8b-instant: 6k tokens/min ❌ (insuficiente para multi-periodo)
        #
        # Con 3,705 tokens/request × 2 periodos = ~7,400 tokens
        # llama-3.3-70b: 30k tokens/min = ~4 requests/min (perfecto)
        provider="groq/llama-3.3-70b-versatile",

        api_token=os.getenv("GROQ_API_KEY"),  # API token for authentication
        schema=HabitacionWeb.model_json_schema(),  # JSON schema of the data model
        extraction_type="schema",  # Type of extraction to perform

        # Prompt optimizado (más conciso = ~10% más rápido)
        instruction=(
            "Extract all hotel rooms with: name, details, "
            "and promotions list (title, description, nightly price)"
        ),

        input_format="markdown",  # Format of the input content
        verbose=DEBUG_CRAWL4AI_VERBOSE,
    )

def fechas_validas(fecha_entrada: date, fecha_salida: date) -> bool:
    hoy = date.today()
    if fecha_entrada < hoy:
        print(f"Fecha de entrada {fecha_entrada} es anterior a hoy {hoy}.")
        return False
    if fecha_salida <= fecha_entrada:
        print(f"Fecha de salida {fecha_salida} debe ser posterior a la entrada {fecha_entrada}.")
        return False
    return True

async def procesar_resultado_scraping(result):
    if not (result.success and result.extracted_content):
        print(f"Error: No hay contenido extraído o extracción no exitosa")
        print(f"Success: {result.success}")
        print(f"Content: {result.extracted_content}")
        print(f"Error en la obtención: {result.error_message}")
        return None

 
    try:
        if DEBUG_COMPARISON_PIPELINE:
            print("Contenido extraído:", result.extracted_content)
        hotel_data = json.loads(result.extracted_content)

        if not hotel_data:
            print("Error: hotel_data está vacío después de parsear JSON")
            return None
            
        # Verificar si es una lista de habitaciones
        if isinstance(hotel_data, list):
            if DEBUG_COMPARISON_PIPELINE:
                print(f"Procesando {len(hotel_data)} habitaciones")
            habitaciones = []
            for h in hotel_data:
                try:
                    habitacion = HabitacionWeb(**h)
                    habitaciones.append(habitacion)
                except Exception as e:
                    print(f"Error procesando habitación: {e}")
                    continue
            
            if not habitaciones:
                print("Error: No se pudo procesar ninguna habitación válida")
                return None
                
            hotel = HotelWeb(
                detalles="Alvear Palace Hotel",
                habitacion=habitaciones
            )
            return hotel
        else:
            print(f"Error: Formato inesperado de datos. Se esperaba lista, se recibió: {type(hotel_data)}")
            return None
    except json.JSONDecodeError as e:
        print(f"Error decodificando JSON: {e}")
        print(f"Contenido raw: {result.extracted_content}")
        return None
    except Exception as e:
        print(f"Error inesperado procesando datos: {e}")
        return None
    



async def fetch_and_process_page(
    crawler: AsyncWebCrawler,
    base_url: str,
    params: dict,
    css_selector: str,
    llm_strategy: LLMExtractionStrategy,
    session_id: str,
    nombre_hotel: str = "Alvear Palace Hotel",
    max_retries: int = 3,
    delay_between_retries: int = 5,
    on_scrape_step: Optional[Callable[[str], None]] = None,
) -> Optional[HotelWeb]:

    url_completa = f"{base_url}?{urlencode(params)}"
    if DEBUG_COMPARISON_PIPELINE:
        print(f"Loading hotel page: {url_completa}...")

    def _notify(step: str):
        if on_scrape_step:
            on_scrape_step(step)

    # Hooks que mapean las etapas internas del crawl a pasos visibles
    async def _before_goto(page, context, url, **kwargs):
        _notify("FETCH")
        return page

    async def _after_goto(page, context, url, response, **kwargs):
        _notify("SCRAPE")
        return page

    async def _before_retrieve_html(page, context, **kwargs):
        _notify("EXTRACT")
        return page

    async def _before_return_html(page, context, html, **kwargs):
        _notify("COMPLETE")
        return page

    _notify("INIT")
    crawler.crawler_strategy.set_hook("before_goto", _before_goto)
    crawler.crawler_strategy.set_hook("after_goto", _after_goto)
    crawler.crawler_strategy.set_hook("before_retrieve_html", _before_retrieve_html)
    crawler.crawler_strategy.set_hook("before_return_html", _before_return_html)

    for intento in range(max_retries):
        try:
        #ejecuta el crawl
            result = await crawler.arun(
                url=url_completa,
                config=CrawlerRunConfig(
                    scan_full_page=False,
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=llm_strategy,
                    css_selector=css_selector,
                    session_id=session_id,

                    # ===== OPTIMIZACIONES DE RENDIMIENTO =====
                    # Timeout: 30s para dar tiempo al LLM y carga completa
                    page_timeout=30000,

                    # TESTING: Volvemos a networkidle para verificar datos completos
                    # - "networkidle": Espera 500ms sin requests (LENTO pero SEGURO)
                    # - "domcontentloaded": Espera DOM listo (RÁPIDO pero puede perder datos dinámicos)
                    # - "load": Espera TODOS los recursos (MEDIO)
                    wait_until="networkidle",

                    # Espera específica para el contenedor de habitaciones
                    # Asegura que el elemento exista antes de capturar
                    # NOTA: css_selector (línea 146) filtra el HTML; wait_for espera a que exista
                    wait_for="css:.thumb-cards_products",  # Selector del contenedor de habitaciones
                ),
            )

            # ============================================================
            # NIVEL 1 — Crawl4AI: ¿llegó la página?
            # ============================================================
            if DEBUG_SCRAPING_PIPELINE:
                html_len = len(result.html) if getattr(result, "html", None) else 0
                md_obj = getattr(result, "markdown", None)
                md_len = len(str(md_obj)) if md_obj else 0
                print(
                    f"[PIPELINE][L1-Crawl] intento={intento + 1} "
                    f"success={result.success} "
                    f"status={getattr(result, 'status_code', 'N/A')} "
                    f"html_len={html_len} markdown_len={md_len} "
                    f"error={getattr(result, 'error_message', None)}"
                )

            # ============================================================
            # NIVEL 2 — Markdown enviado al LLM (siempre que haya algo)
            # ============================================================
            if DEBUG_SCRAPING_PIPELINE and getattr(result, "markdown", None):
                markdown_content = str(result.markdown)
                num_chars = len(markdown_content)
                estimated_tokens = num_chars // 4
                print(
                    f"[PIPELINE][L2-Markdown] chars={num_chars:,} "
                    f"tokens_estimados=~{estimated_tokens:,} "
                    f"preview={markdown_content[:200]!r}"
                )

            # Archivo separado (opt-in, default False) — útil para inspeccionar markdown completo
            if result.success and DEBUG_LLM_MARKDOWN:
                try:
                    import datetime
                    markdown_content = result.markdown if hasattr(result, 'markdown') else result.cleaned_html
                    num_chars = len(str(markdown_content))
                    estimated_tokens = num_chars // 4
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    debug_file = f"debug_llm_input_{timestamp}.txt"
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write("="*80 + "\nDEBUG: CONTENIDO ENVIADO AL LLM\n" + "="*80 + "\n\n")
                        f.write(f"Caracteres: {num_chars:,}\nTokens estimados: {estimated_tokens:,}\nURL: {url_completa}\n\n")
                        f.write("="*80 + "\nCONTENIDO MARKDOWN:\n" + "="*80 + "\n\n")
                        f.write(str(markdown_content))
                    print(f"[DEBUG] Contenido LLM guardado en: {debug_file}")
                except Exception as e:
                    print(f"[DEBUG] Error guardando debug: {e}")

            # ============================================================
            # NIVEL 3 — Respuesta del LLM (Groq)
            # ============================================================
            habitaciones_data = None
            if result.success and result.extracted_content:
                raw = result.extracted_content
                if DEBUG_SCRAPING_PIPELINE:
                    preview = raw[:500] + ("..." if len(raw) > 500 else "")
                    print(f"[PIPELINE][L3-Groq] raw_len={len(raw)} raw_preview={preview!r}")
                try:
                    habitaciones_data = json.loads(raw)
                    if DEBUG_SCRAPING_PIPELINE:
                        parsed_len = len(habitaciones_data) if hasattr(habitaciones_data, '__len__') else 'N/A'
                        print(f"[PIPELINE][L3-Groq] json_ok tipo={type(habitaciones_data).__name__} len={parsed_len}")
                except json.JSONDecodeError as e:
                    if DEBUG_SCRAPING_PIPELINE:
                        print(f"[PIPELINE][L3-Groq] ❌ json_invalido: {e}")
                    habitaciones_data = None

                if habitaciones_data and len(habitaciones_data) > 0:
                    print(f"Datos extraídos exitosamente en el intento {intento + 1}")
                    return await procesar_resultado_scraping(result)
                elif DEBUG_SCRAPING_PIPELINE:
                    print(f"[PIPELINE][L3-Groq] ❌ marcado_incompleto habitaciones_data={habitaciones_data!r}")
            elif DEBUG_SCRAPING_PIPELINE:
                razon = "result.success=False" if not result.success else "extracted_content vacío"
                print(f"[PIPELINE][L3-Groq] ⏭️  skipped — {razon}")

            print(f"Intento {intento + 1} falló o datos incompletos. Esperando {delay_between_retries} segundos...")
            await asyncio.sleep(delay_between_retries)

        except Exception as e:
            print(f"Error en intento {intento + 1}: {str(e)}")
            if intento < max_retries - 1:
                await asyncio.sleep(delay_between_retries)
            else:
                raise Exception(f"Fallaron todos los intentos de extracción: {str(e)}\nURL: {url_completa}")

    raise Exception(f"No se pudieron obtener datos completos después de todos los reintentos\nURL: {url_completa}")
