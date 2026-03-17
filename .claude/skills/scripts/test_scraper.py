#!/usr/bin/env python
"""
test_scraper.py - Testing rápido del scraper con tiempos

Uso:
    python test_scraper.py [hotel] [fecha_entrada] [fecha_salida] [adultos] [ninos]

Ejemplos:
    python test_scraper.py
    python test_scraper.py alvear 01-02-2026 05-02-2026 2 1
"""

import sys
import os
import asyncio
import time
import json
from datetime import date, timedelta, datetime
from pathlib import Path

# Agregar Hoteles/ al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "Hoteles"))

from ScrawlingChinese.crawler import crawl_alvear

# Dict para multi-sitio (futuro)
CRAWLERS = {
    "alvear": crawl_alvear,
    # "marriott": crawl_marriott,  # Futuro
}


def parsear_fecha(fecha_str):
    """
    Parsea fecha DD-MM-YYYY → date object.

    Args:
        fecha_str: String en formato DD-MM-YYYY

    Returns:
        date object

    Raises:
        ValueError si el formato es incorrecto
    """
    try:
        return datetime.strptime(fecha_str, "%d-%m-%Y").date()
    except ValueError:
        raise ValueError(f"Formato de fecha inválido: '{fecha_str}'. Usar DD-MM-YYYY (ej: 01-02-2026)")


def main():
    # Parsear argumentos con defaults
    hotel = sys.argv[1] if len(sys.argv) > 1 else "alvear"
    fecha_entrada_str = sys.argv[2] if len(sys.argv) > 2 else None
    fecha_salida_str = sys.argv[3] if len(sys.argv) > 3 else None
    adultos = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    ninos = int(sys.argv[5]) if len(sys.argv) > 5 else 0

    # Defaults inteligentes para fechas
    if not fecha_entrada_str:
        fecha_entrada = date.today() + timedelta(days=1)  # Mañana
    else:
        fecha_entrada = parsear_fecha(fecha_entrada_str)

    if not fecha_salida_str:
        fecha_salida = fecha_entrada + timedelta(days=1)  # Día después de entrada
    else:
        fecha_salida = parsear_fecha(fecha_salida_str)

    # Validar fechas
    if fecha_salida <= fecha_entrada:
        print("❌ Error: Fecha de salida debe ser posterior a fecha de entrada")
        sys.exit(1)

    # Verificar que el crawler existe
    if hotel not in CRAWLERS:
        print(f"❌ Error: Hotel '{hotel}' no configurado.")
        print(f"Hoteles disponibles: {', '.join(CRAWLERS.keys())}")
        sys.exit(1)

    crawler_func = CRAWLERS[hotel]

    # Mostrar configuración
    print(f"\n🔍 Test Scraper - Hotel: {hotel}")
    print(f"📅 Fechas: {fecha_entrada.strftime('%d-%m-%Y')} → {fecha_salida.strftime('%d-%m-%Y')}")
    print(f"👥 Huéspedes: {adultos} adultos, {ninos} niños\n")

    # Ejecutar scraping con timer
    print("⏱️  Ejecutando scraping...")
    start_time = time.time()

    try:
        resultado = asyncio.run(crawler_func(
            fecha_entrada=fecha_entrada.strftime("%Y-%m-%d"),
            fecha_salida=fecha_salida.strftime("%Y-%m-%d"),
            adultos=adultos,
            ninos=ninos
        ))
    except Exception as e:
        end_time = time.time()
        print(f"❌ Error durante scraping (después de {end_time - start_time:.2f}s):")
        print(f"   {str(e)}")
        sys.exit(1)

    end_time = time.time()
    elapsed = end_time - start_time

    # Mostrar resultados
    print(f"✅ Completado en {elapsed:.2f}s\n")

    num_habitaciones = len(resultado.habitacion)
    print(f"📊 Resultados:")
    print(f"   - {num_habitaciones} habitaciones extraídas\n")

    if num_habitaciones == 0:
        print("⚠️  No se extrajo ninguna habitación.")
        print("   Ver docs/scraper/troubleshooting.md para debugging")
    else:
        # Mostrar primeras 3 habitaciones
        for i, hab in enumerate(resultado.habitacion[:3], 1):
            print(f"   {i}. {hab.nombre}")

            if hab.combos:
                precio_min = min([combo.precio for combo in hab.combos])
                print(f"      💵 Precio más barato: ${precio_min:.2f} USD")
            else:
                print(f"      ⚠️  Sin precios disponibles")

            print()

    # Guardar resultado en JSON
    # Crear directorio tmp/ si no existe
    tmp_dir = Path(__file__).parent.parent.parent / "tmp"
    tmp_dir.mkdir(exist_ok=True)

    # Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_file = tmp_dir / f"test-scraper-{timestamp}.json"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(resultado.model_dump(), f, indent=2, ensure_ascii=False)

    print(f"💾 Resultado guardado en: {json_file}")
    print("\n---")
    print("🌐 Multi-sitio: Para testear otros hoteles, agregar configuración en ScrawlingChinese/config.py")
    print()


if __name__ == "__main__":
    main()
