import json
import os
from typing import List, Set, Tuple
from urllib.parse import urlencode
import asyncio
from typing import Optional

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
        verbose=True,  # Enable verbose logging
    )


def get_llm_strategy() -> LLMExtractionStrategy:
    """
    Returns the configuration for the language model extraction strategy.

    Returns:
        LLMExtractionStrategy: The settings for how to extract data using LLM.
    """
    # https://docs.crawl4ai.com/api/strategies/#llmextractionstrategy
    
    return LLMExtractionStrategy(
        provider="groq/deepseek-r1-distill-llama-70b",  # Name of the LLM provider
        api_token=os.getenv("GROQ_API_KEY"),  # API token for authentication
        schema=HabitacionWeb.model_json_schema(),  # JSON schema of the data model
        extraction_type="schema",  # Type of extraction to perform
        instruction=(
        "Extrae todas las habitaciones con su nombre, su detalle, "
        "y una lista de promociones con su titulo (ejemplo 'desayuno incluido', 'cancelación gratuita', etc.),"
        "descripcion y precio por noche "
        ),  # Instructions for the LLM
        input_format="markdown",  # Format of the input content
        verbose=True,  # Enable verbose logging
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
        print("Contenido extraído:", result.extracted_content)  
        hotel_data = json.loads(result.extracted_content)

        if not hotel_data:
            print("Error: hotel_data está vacío después de parsear JSON")
            return None
            
        # Verificar si es una lista de habitaciones
        if isinstance(hotel_data, list):
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
    delay_between_retries: int = 5
) -> Optional[HotelWeb]:
    
    url_completa = f"{base_url}?{urlencode(params)}"
    print(f"Loading hotel page: {url_completa}...")

    
    for intento in range(max_retries):
        try:
        #ejecuta el crawl
            result = await crawler.arun(
                url=url_completa,
                config=CrawlerRunConfig(
                    scan_full_page=True,
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=llm_strategy,
                    css_selector=css_selector,
                    session_id=session_id,
                    page_timeout=30000,  # 30 segundos de timeout
                    wait_until="networkidle"  # espera hasta que no haya actividad de red
                ),
            )
            # Verifica si los datos están completos
            if result.success and result.extracted_content:
                habitaciones_data = json.loads(result.extracted_content)
                if habitaciones_data and len(habitaciones_data) > 0:
                    print(f"Datos extraídos exitosamente en el intento {intento + 1}")
                    return await procesar_resultado_scraping(result)
            
            print(f"Intento {intento + 1} falló o datos incompletos. Esperando {delay_between_retries} segundos...")
            await asyncio.sleep(delay_between_retries)

        except Exception as e:
            print(f"Error en intento {intento + 1}: {str(e)}")
            if intento < max_retries - 1:
                await asyncio.sleep(delay_between_retries)
            else:
                raise Exception(f"Fallaron todos los intentos de extracción: {str(e)}")

    raise Exception("No se pudieron obtener datos completos después de todos los reintentos")
