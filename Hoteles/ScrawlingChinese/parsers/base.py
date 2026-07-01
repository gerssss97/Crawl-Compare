from typing import Optional, Protocol, runtime_checkable
from crawl4ai import LLMExtractionStrategy
from Models.hotelWeb import HotelWeb


@runtime_checkable
class RoomParser(Protocol):
    def get_extraction_strategy(self) -> Optional[LLMExtractionStrategy]: ...
    async def parse(self, result, url: str) -> Optional[HotelWeb]: ...
