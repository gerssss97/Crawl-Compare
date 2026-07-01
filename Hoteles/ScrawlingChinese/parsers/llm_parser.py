import json
import os
from typing import Optional

from crawl4ai import LLMExtractionStrategy
from Models.hotelWeb import HotelWeb, HabitacionWeb


class LLMParser:
    """Extrae habitaciones mandando el HTML al LLM (Groq). Flujo actual del Alvear."""

    def __init__(self, config):
        self._config = config

    def get_extraction_strategy(self) -> LLMExtractionStrategy:
        return LLMExtractionStrategy(
            provider="groq/llama-3.3-70b-versatile",
            api_token=os.getenv("GROQ_API_KEY"),
            schema=HabitacionWeb.model_json_schema(),
            extraction_type="schema",
            instruction=self._config.LLM_INSTRUCTION,
            input_format="markdown",
            verbose=False,
        )

    async def parse(self, result, url: str) -> Optional[HotelWeb]:
        if not (result.success and result.extracted_content):
            return None

        try:
            datos = json.loads(result.extracted_content)
        except json.JSONDecodeError:
            return None

        if not datos or not isinstance(datos, list):
            return None

        habitaciones = []
        for item in datos:
            try:
                habitaciones.append(HabitacionWeb(**item))
            except Exception:
                continue

        if not habitaciones:
            return None

        return HotelWeb(
            detalles=self._config.NOMBRE_HOTEL,
            habitacion=habitaciones,
            url_visitada=url,
        )
