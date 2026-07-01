#!/usr/bin/env python
"""
test_scraper.py - Testing rápido del scraper con tiempos

Uso:
    python test_scraper.py [hotel] [fecha_entrada] [fecha_salida] [adultos] [args...]

Alvear:
    python test_scraper.py alvear 01-02-2026 05-02-2026 2 1
    python test_scraper.py alvear 01-02-2026 05-02-2026 2 0 --parser=dom

Faena (los args extras son las EDADES de los niños, no la cantidad):
    python test_scraper.py faena 28-06-2026 29-06-2026 2
    python test_scraper.py faena 28-06-2026 29-06-2026 2 16 2
    python test_scraper.py faena 28-06-2026 29-06-2026 2 16 2 --parser=dom
"""

import sys
import os
import asyncio
import time
import json
from datetime import date, timedelta, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "Hoteles"))

from ScrawlingChinese.crawler import crawl_alvear, crawl_faena, CRAWLERS


def parsear_fecha(fecha_str):
    try:
        return datetime.strptime(fecha_str, "%d-%m-%Y").date()
    except ValueError:
        raise ValueError(f"Formato de fecha inválido: '{fecha_str}'. Usar DD-MM-YYYY (ej: 01-02-2026)")


def extraer_parser_type(args: list) -> tuple[list, str | None]:
    """Extrae --parser=llm|dom de la lista de args y devuelve (args_restantes, parser_type).
    Si no se especifica --parser, devuelve None para que make_scraper use DEFAULT_PARSER del SiteConfig."""
    parser_type = None
    restantes = []
    for arg in args:
        if arg.startswith("--parser="):
            parser_type = arg.split("=", 1)[1]
        else:
            restantes.append(arg)
    return restantes, parser_type


def main():
    args_raw = sys.argv[1:]
    args, parser_type = extraer_parser_type(args_raw)

    hotel            = args[0] if len(args) > 0 else "alvear"
    fecha_entrada_str = args[1] if len(args) > 1 else None
    fecha_salida_str  = args[2] if len(args) > 2 else None
    adultos          = int(args[3]) if len(args) > 3 else 2
    args_extra       = args[4:]  # ninos (alvear) o edades_ninos (faena)

    if not fecha_entrada_str:
        fecha_entrada = date.today() + timedelta(days=1)
    else:
        fecha_entrada = parsear_fecha(fecha_entrada_str)

    if not fecha_salida_str:
        fecha_salida = fecha_entrada + timedelta(days=1)
    else:
        fecha_salida = parsear_fecha(fecha_salida_str)

    if fecha_salida <= fecha_entrada:
        print("Error: Fecha de salida debe ser posterior a fecha de entrada")
        sys.exit(1)

    if hotel not in CRAWLERS:
        print(f"Error: Hotel '{hotel}' no configurado.")
        print(f"Hoteles disponibles: {', '.join(CRAWLERS.keys())}")
        sys.exit(1)

    fecha_in_str = fecha_entrada.strftime("%Y-%m-%d")
    fecha_out_str = fecha_salida.strftime("%Y-%m-%d")

    print(f"\nTest Scraper — Hotel: {hotel} | Parser: {parser_type}")
    print(f"Fechas: {fecha_entrada.strftime('%d-%m-%Y')} -> {fecha_salida.strftime('%d-%m-%Y')}")
    print(f"Adultos: {adultos}")

    if hotel == "faena":
        edades_ninos = [int(e) for e in args_extra]
        if edades_ninos:
            print(f"Edades niños: {edades_ninos}")
        print()
        coro = crawl_faena(
            fecha_in_str, fecha_out_str,
            adultos=adultos,
            edades_ninos=edades_ninos,
            parser_type=parser_type,
        )
    else:
        ninos = int(args_extra[0]) if args_extra else 0
        print(f"Niños: {ninos}")
        print()
        coro = crawl_alvear(
            fecha_in_str, fecha_out_str,
            adultos=adultos,
            niños=ninos,
            parser_type=parser_type,
        )

    print("Ejecutando scraping...")
    start_time = time.time()

    try:
        resultado = asyncio.run(coro)
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"Error durante scraping (despues de {elapsed:.2f}s): {e}")
        sys.exit(1)

    elapsed = time.time() - start_time
    print(f"Completado en {elapsed:.2f}s\n")

    num_habitaciones = len(resultado.habitacion)
    print(f"Resultados: {num_habitaciones} habitaciones extraidas\n")

    if num_habitaciones == 0:
        print("No se extrajo ninguna habitacion.")
        print("Ver docs/scraper/troubleshooting.md para debugging")
    else:
        for i, hab in enumerate(resultado.habitacion[:3], 1):
            print(f"  {i}. {hab.nombre}")
            if hab.combos:
                precio_min = min(c.precio for c in hab.combos)
                if hab.impuestos is not None:
                    print(f"     Base: ${precio_min:.2f} USD")
                    print(f"     Taxes: ${hab.impuestos:.2f} USD")
                    total = hab.precio_total()
                    print(f"     Total: ${total:.2f} USD")
                else:
                    print(f"     Precio: ${precio_min:.2f} USD")
            else:
                print(f"     Sin precios disponibles")
            print()

    tmp_dir = Path(__file__).parent.parent.parent / "tmp"
    tmp_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_file = tmp_dir / f"test-scraper-{hotel}-{parser_type}-{timestamp}.json"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(resultado.model_dump(), f, indent=2, ensure_ascii=False)

    print(f"Resultado guardado en: {json_file}")


if __name__ == "__main__":
    main()
