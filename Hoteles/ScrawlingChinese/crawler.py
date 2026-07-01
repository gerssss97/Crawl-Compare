from typing import Callable, Optional
from dotenv import load_dotenv

from Models.hotelWeb import HotelWeb
from .site_configs import AlvearConfig, FaenaConfig
from .parsers import LLMParser, DOMParser
from .utils.hotel_scraper import HotelScraper

load_dotenv()


_SITE_CONFIGS = {
    "alvear": AlvearConfig,
    "faena":  FaenaConfig,
}


def make_scraper(hotel: str, parser_type: str = None) -> HotelScraper:
    """
    Factory: combina un SiteConfig (qué hotel) con un RoomParser (cómo parsear).

    Args:
        hotel: clave del hotel ("alvear", "faena", ...)
        parser_type: "llm" o "dom". Si es None, usa SiteConfig.DEFAULT_PARSER.
    """
    if hotel not in _SITE_CONFIGS:
        raise KeyError(f"Hotel '{hotel}' no tiene SiteConfig registrado.")

    config = _SITE_CONFIGS[hotel]()
    effective_parser = parser_type or getattr(config, "DEFAULT_PARSER", "llm")
    parser = LLMParser(config) if effective_parser == "llm" else DOMParser(config)
    return HotelScraper(config, parser)


async def crawl_alvear(
    fecha_ingreso: str,
    fecha_egreso: str,
    adultos: int,
    niños: int,
    parser_type: str = None,
    on_scrape_step: Optional[Callable[[str], None]] = None,
) -> Optional[HotelWeb]:
    scraper = make_scraper("alvear", parser_type)
    return await scraper.crawl(
        fecha_ingreso,
        fecha_egreso,
        on_scrape_step=on_scrape_step,
        adultos=adultos,
        ninos=niños,
    )


async def crawl_faena(
    fecha_ingreso: str,
    fecha_egreso: str,
    adultos: int,
    edades_ninos: list = None,
    parser_type: str = None,
    on_scrape_step: Optional[Callable[[str], None]] = None,
) -> Optional[HotelWeb]:
    scraper = make_scraper("faena", parser_type)
    return await scraper.crawl(
        fecha_ingreso,
        fecha_egreso,
        on_scrape_step=on_scrape_step,
        adultos=adultos,
        edades_ninos=edades_ninos,
    )


CRAWLERS = {
    "alvear": crawl_alvear,
    "faena":  crawl_faena,
}


def get_crawler(hotel_nombre: str):
    if hotel_nombre not in CRAWLERS:
        raise KeyError(f"Hotel '{hotel_nombre}' no tiene crawler configurado.")
    return CRAWLERS[hotel_nombre]
