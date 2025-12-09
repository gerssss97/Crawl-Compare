import asyncio
from crawl4ai import AsyncWebCrawler
from dotenv import load_dotenv
from .config import BASE_URL, CSS_SELECTOR
from Models.hotelExcel import *
from Models.hotelWeb import HotelWeb

from .utils.scraper_utils import (
    fetch_and_process_page,
    get_browser_config,
    get_llm_strategy,
)

load_dotenv()


async def crawl_alvear(fecha_ingreso,fecha_egreso,adultos,niños) -> Optional[HotelWeb] :
    browser_config = get_browser_config()
    llm_strategy = get_llm_strategy()
    session_id = "venue_crawl_session"

    # Initialize state variables
    params_busqueda = {
        "adult": adultos,
        "child": niños,
        "arrive": fecha_ingreso,
        "depart": fecha_egreso,
        "chain": 24447,
        "hotel": 6933,
        "currency": "USD",
        "level": "hotel",
        "locale": "en-US",
        "productcurrency": "USD",
        "rooms": 1,
        "src": 30,
    }

    # Start the web crawler context
    # https://docs.crawl4ai.com/api/async-webcrawler/#asyncwebcrawler
    async with AsyncWebCrawler(config=browser_config) as crawler:
    
        # Fetch and process data from the current page
        hotel = await fetch_and_process_page(
            crawler,
            BASE_URL,
            params_busqueda,
            CSS_SELECTOR,
            llm_strategy,
            session_id,
        )
        #llm_strategy.show_usage()
    return hotel




