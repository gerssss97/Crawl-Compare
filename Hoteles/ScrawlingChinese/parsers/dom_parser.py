import re
from typing import Optional

from Models.hotelWeb import HotelWeb, HabitacionWeb, ComboPrecio


class DOMParser:
    """Extrae habitaciones con BeautifulSoup sobre HTML crudo. Sin LLM."""

    def __init__(self, config):
        self._config = config

    def get_extraction_strategy(self):
        # Sin strategy: Crawl4AI devuelve HTML crudo en result.html
        return None

    async def parse(self, result, url: str) -> Optional[HotelWeb]:
        nombre_sel = self._config.DOM_NOMBRE_HAB_SEL
        precio_sel = self._config.DOM_PRECIO_SEL

        if not nombre_sel or not precio_sel:
            raise NotImplementedError(
                f"DOMParser no soportado para {self._config.NOMBRE_HOTEL}: "
                "DOM_NOMBRE_HAB_SEL y DOM_PRECIO_SEL no están definidos en su SiteConfig."
            )

        if not result.success or not result.html:
            return None

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(result.html, "html.parser")

        nombres = [el.get_text(strip=True) for el in soup.select(nombre_sel)]
        precios_raw = [el.get_text(strip=True) for el in soup.select(precio_sel)]

        if not nombres:
            return None

        taxes_sel = getattr(self._config, "DOM_TAXES_SEL", None)
        taxes_raw = []
        if taxes_sel:
            taxes_raw = [el.get_text(strip=True) for el in soup.select(taxes_sel)]
            if len(taxes_raw) != len(nombres):
                raise ValueError(
                    f"[DOMParser] Mismatch taxes vs habitaciones: "
                    f"{len(taxes_raw)} taxes vs {len(nombres)} habitaciones"
                )

        habitaciones = []
        for i, nombre in enumerate(nombres):
            precio_str = precios_raw[i] if i < len(precios_raw) else "0"
            precio_float = _parsear_precio(precio_str)
            impuestos = _parsear_precio(taxes_raw[i]) if taxes_raw else None

            habitaciones.append(HabitacionWeb(
                nombre=nombre,
                detalles=None,
                combos=[ComboPrecio(
                    titulo="Tarifa disponible",
                    descripcion=precio_str,
                    precio=precio_float,
                )],
                impuestos=impuestos,
            ))

        return HotelWeb(
            detalles=self._config.NOMBRE_HOTEL,
            habitacion=habitaciones,
            url_visitada=url,
        )



def _parsear_precio(texto: str) -> float:
    """Extrae el primer número flotante de un string de precio."""
    match = re.search(r"\d+\.?\d*", texto.replace(",", ""))
    return float(match.group()) if match else 0.0
