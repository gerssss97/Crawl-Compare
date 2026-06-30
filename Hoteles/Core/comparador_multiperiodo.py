"""Comparador multi-periodo con scraping secuencial."""

import asyncio
from debug_config import DEBUG_COMPARISON_PIPELINE
from typing import List
from datetime import date
from Models.hotelExcel import Periodo, HotelExcel
from Models.hotelWeb import HabitacionWeb
from Core.servicio_habitaciones import inferir_periodos_desde_fechas
from Core.comparador import obtener_mejor_match
from Core.controller import dar_hotel_web


class ResultadoPeriodo:
    """Resultado de comparación para un periodo específico."""

    def __init__(self, periodo: Periodo, precio_excel: float | str,
                 precio_web: float, diferencia: float, coincide: bool,
                 fecha_inicio_real: date = None, fecha_fin_real: date = None,
                 error_msg: str = None, error_url: str = None,
                 url_visitada: str = None):
        self.periodo = periodo
        self.precio_excel = precio_excel
        self.precio_web = precio_web
        self.diferencia = diferencia
        self.coincide = coincide
        self.fecha_inicio_real = fecha_inicio_real  # Fecha específica ingresada (overlap con periodo)
        self.fecha_fin_real = fecha_fin_real  # Fecha específica ingresada (overlap con periodo)
        self.error_msg = error_msg  # Mensaje de error si el scraping falló
        self.error_url = error_url  # URL que se intentó acceder (caso error)
        self.url_visitada = url_visitada  # URL real scrapeada en este periodo (caso éxito)


class ResultadoComparacionMultiperiodo:
    """Resultado completo de comparación multi-periodo."""

    def __init__(self, habitacion_excel_nombre: str,
                 habitacion_web_matcheada: HabitacionWeb,
                 periodos: List[ResultadoPeriodo],
                 tiene_discrepancias: bool,
                 mensaje_match: str = None):
        self.habitacion_excel_nombre = habitacion_excel_nombre
        self.habitacion_web_matcheada = habitacion_web_matcheada
        self.periodos = periodos
        self.tiene_discrepancias = tiene_discrepancias
        self.mensaje_match = mensaje_match


async def comparar_multiperiodo(
    habitacion_unificada,  # HabitacionUnificada
    fecha_entrada: date,
    fecha_salida: date,
    adultos: int,
    ninos: int,
    hotel: HotelExcel,
    site_config=None,  # FaenaConfig | AlvearConfig — extraer_precio_web(hab_web, nombre_excel) -> float
    on_progress=None,  # callable(periodo_actual: int, total: int, estado: str) | None
    on_scrape_step=None,  # callable(step: str) | None - pasos dentro del scraping
) -> ResultadoComparacionMultiperiodo:
    """Compara habitación Excel vs Web para múltiples periodos.

    Flujo:
    1. Inferir periodos aplicables al rango de fechas
    2. Para cada periodo (SECUENCIAL):
        - Calcular rango de fechas específico del periodo
        - Scrape web con esas fechas (force_fresh=True)
        - Si primer periodo: fuzzy matching → guardar habitación matcheada
        - Si periodo subsiguiente: reutilizar habitación matcheada
        - Extraer precio_web del combo[0]
        - Comparar con precio_excel
    3. Construir resultado consolidado

    Args:
        habitacion_unificada: HabitacionUnificada con variantes
        fecha_entrada: Fecha entrada de reserva
        fecha_salida: Fecha salida de reserva
        adultos: Número de adultos
        ninos: Número de niños
        hotel: Hotel actual (para buscar periodos)
        site_config: FaenaConfig | AlvearConfig — requerido para extraer precios web

    Returns:
        ResultadoComparacionMultiperiodo con breakdown por periodo

    Raises:
        ValueError: Si no hay periodos aplicables o si falla el matching
    """
    # Guard: verificar que site_config sea proporcionado
    if site_config is None:
        raise ValueError("site_config es requerido para comparar_multiperiodo")

    # Paso 1: Inferir periodos aplicables
    periodos_aplicables = inferir_periodos_desde_fechas(fecha_entrada, fecha_salida, hotel)

    if not periodos_aplicables:
        raise ValueError(f"No se encontraron periodos aplicables para {fecha_entrada} a {fecha_salida}")

    if DEBUG_COMPARISON_PIPELINE:
        print(f"\n{'='*60}")
        print(f"COMPARACIÓN MULTI-PERIODO: {habitacion_unificada.nombre}")
        print(f"Periodos detectados: {len(periodos_aplicables)}")
        print(f"{'='*60}\n")

    resultados_periodos = []
    habitacion_web_matcheada = None
    mensaje_match = None

    total_periodos = len(periodos_aplicables)

    # Paso 2: Loop secuencial por cada periodo
    for idx, periodo in enumerate(periodos_aplicables, start=1):
        if DEBUG_COMPARISON_PIPELINE:
            print(f"\n--- PERIODO {idx}/{total_periodos} ---")

        if on_progress:
            on_progress(idx, total_periodos, f"Scrapeando periodo {idx}/{total_periodos}...")

        try:
            # Calcular fechas específicas para scraping (overlap entre reserva y periodo)
            fecha_scrape_inicio = max(fecha_entrada, periodo.fecha_inicio)
            fecha_scrape_fin = min(fecha_salida, periodo.fecha_fin)

            # Convertir a formato DD-MM-YYYY
            fecha_inicio_str = fecha_scrape_inicio.strftime("%d-%m-%Y")
            fecha_fin_str = fecha_scrape_fin.strftime("%d-%m-%Y")

            if DEBUG_COMPARISON_PIPELINE:
                print(f"Scraping con fechas: {fecha_inicio_str} a {fecha_fin_str}")

            # Scrape web (TESTING: usar force_pickle para tests rápidos)
            hotel_web = await dar_hotel_web(
                fecha_inicio_str,
                fecha_fin_str,
                adultos,
                ninos,
                force_fresh=False,     # Cambia a True para scraping fresco
                use_pickle=False,      # False para multi-periodo
                force_pickle=False,    # MODO TESTING: Carga pickle directo
                on_scrape_step=on_scrape_step,
            )

            if not hotel_web or not hotel_web.habitacion:
                raise ValueError(f"Error scrapeando periodo {idx}")

            # Fuzzy matching en el primer periodo exitoso (idx==1 o si el anterior falló)
            if habitacion_web_matcheada is None:
                print("→ Realizando fuzzy matching...")
                if on_progress:
                    on_progress(idx, total_periodos, f"Periodo {idx}: buscando habitacion...")
                habitacion_web_matcheada, mensaje_match = obtener_mejor_match(
                    habitacion_unificada.nombre,
                    hotel_web.habitacion
                )

                if not habitacion_web_matcheada:
                    raise ValueError(f"No se encontró match para '{habitacion_unificada.nombre}'")

                print(f"→ Match encontrado: {habitacion_web_matcheada.nombre}")
            else:
                print(f"→ Reusando habitación matcheada: {habitacion_web_matcheada.nombre}")

                # Buscar la misma habitación en los resultados del scraping actual
                habitacion_actual = None
                for hab in hotel_web.habitacion:
                    if hab.nombre == habitacion_web_matcheada.nombre:
                        habitacion_actual = hab
                        break

                if not habitacion_actual:
                    raise ValueError(
                        f"Habitación '{habitacion_web_matcheada.nombre}' no encontrada en periodo {idx}"
                    )

                habitacion_web_matcheada = habitacion_actual

            # Extraer precio web delegando al site_config
            precio_web = site_config.extraer_precio_web(habitacion_web_matcheada, habitacion_unificada.nombre)
            print(f"→ Precio web: ${precio_web:.2f}")

            # Obtener precio Excel para este periodo
            precio_excel = habitacion_unificada.precio_para_periodo(periodo.id)

            if precio_excel is None:
                raise ValueError(f"No se encontró precio Excel para periodo {idx} (ID: {periodo.id})")

            print(f"→ Precio Excel: {precio_excel}")

            # Comparar precios (solo si Excel tiene precio numérico)
            if isinstance(precio_excel, (int, float)):
                diferencia = abs(float(precio_excel) - precio_web)
                coincide = diferencia < 1.0  # Diferencia menor a $1 = coincide
                print(f"→ Diferencia: ${diferencia:.2f} ({'COINCIDE' if coincide else 'DISCREPANCIA'})")
            else:
                # Precio Excel es leyenda (e.g., "closing agreement")
                diferencia = 0.0
                coincide = True  # No comparamos leyendas
                print(f"→ Precio Excel es leyenda: {precio_excel}")

            estado_periodo = "OK" if coincide else "DISCREPANCIA"
            if on_progress:
                on_progress(idx, total_periodos, f"Periodo {idx}: {estado_periodo}")

            # Guardar resultado del periodo con fechas específicas
            resultados_periodos.append(ResultadoPeriodo(
                periodo=periodo,
                precio_excel=precio_excel,
                precio_web=precio_web,
                diferencia=diferencia,
                coincide=coincide,
                fecha_inicio_real=fecha_scrape_inicio,
                fecha_fin_real=fecha_scrape_fin,
                url_visitada=hotel_web.url_visitada,
            ))

        except Exception as e:
            # Error en periodo individual - continuar con los demás
            error_str = str(e)
            print(f"ERROR en periodo {idx}: {error_str}")
            print("→ Continuando con siguiente periodo...")
            if on_progress:
                on_progress(idx, total_periodos, f"Periodo {idx}: error")

            # Calcular fechas específicas incluso en error (para mostrarlas en tabla)
            fecha_scrape_inicio = max(fecha_entrada, periodo.fecha_inicio)
            fecha_scrape_fin = min(fecha_salida, periodo.fecha_fin)

            # Extraer URL del mensaje de error si está presente.
            # El scraper embebe la URL real que intentó visitar (scraper_utils.py),
            # asi que la tomamos de ahi en vez de reconstruirla a mano.
            error_url = None
            error_msg_clean = error_str
            if "\nURL: " in error_str:
                partes = error_str.split("\nURL: ", 1)
                error_msg_clean = partes[0]
                error_url = partes[1].strip()

            # Agregar resultado con error
            resultados_periodos.append(ResultadoPeriodo(
                periodo=periodo,
                precio_excel="Error",
                precio_web=0.0,
                diferencia=0.0,
                coincide=False,
                fecha_inicio_real=fecha_scrape_inicio,
                fecha_fin_real=fecha_scrape_fin,
                error_msg=error_msg_clean,
                error_url=error_url,
            ))

        # Delay entre requests para evitar IP ban (excepto en último periodo)
        if idx < len(periodos_aplicables):
            import os
            delay_seconds = int(os.getenv("SCRAPING_DELAY_SECONDS", "2"))
            print(f"→ Esperando {delay_seconds}s antes del siguiente periodo...")
            await asyncio.sleep(delay_seconds)

    # Paso 3: Determinar si hay discrepancias globales
    tiene_discrepancias = any(not r.coincide for r in resultados_periodos)

    print(f"\n{'='*60}")
    print(f"RESULTADO: {'DISCREPANCIAS' if tiene_discrepancias else 'TODO COINCIDE'}")
    print(f"{'='*60}\n")

    # Construir resultado consolidado
    return ResultadoComparacionMultiperiodo(
        habitacion_excel_nombre=habitacion_unificada.nombre,
        habitacion_web_matcheada=habitacion_web_matcheada,
        periodos=resultados_periodos,
        tiene_discrepancias=tiene_discrepancias,
        mensaje_match=mensaje_match
    )
