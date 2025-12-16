"""Servicio para unificación de habitaciones e inferencia de periodos."""

from Models.habitacion_unificada import HabitacionUnificada
from Models.hotelExcel import HabitacionExcel, HotelExcel, Periodo
from typing import List, Dict
from datetime import date


def unificar_habitaciones(habitaciones: List[HabitacionExcel]) -> List[HabitacionUnificada]:
    """Unifica habitaciones con el mismo nombre en una sola HabitacionUnificada.

    Esta función agrupa habitaciones que tienen el mismo nombre (normalizadas a
    minúsculas) pero diferentes precios y periodos, creando una HabitacionUnificada
    por cada nombre único.

    Args:
        habitaciones: Lista de HabitacionExcel (puede contener duplicados por nombre)

    Returns:
        Lista de HabitacionUnificada sin duplicados

    Ejemplo:
        Input: [
            HabitacionExcel(nombre="dbl superior", precio=150, periodo_ids={1}),
            HabitacionExcel(nombre="dbl superior", precio=180, periodo_ids={2}),
            HabitacionExcel(nombre="sgl standard", precio=120, periodo_ids={1})
        ]

        Output: [
            HabitacionUnificada(nombre="dbl superior", variantes=[hab1, hab2]),
            HabitacionUnificada(nombre="sgl standard", variantes=[hab3])
        ]
    """
    # Agrupar por nombre normalizado
    grupos: Dict[str, List[HabitacionExcel]] = {}

    for hab in habitaciones:
        nombre_norm = hab.nombre.lower().strip()
        if nombre_norm not in grupos:
            grupos[nombre_norm] = []
        grupos[nombre_norm].append(hab)

    # Crear HabitacionUnificada para cada grupo
    resultado = []
    for nombre, variantes in grupos.items():
        resultado.append(HabitacionUnificada(
            nombre=nombre,
            variantes=variantes
        ))

    return resultado


def inferir_periodos_desde_fechas(
    fecha_entrada: date,
    fecha_salida: date,
    hotel: HotelExcel
) -> List[Periodo]:
    """Infiere qué periodos del hotel aplican para un rango de fechas dado.

    Un periodo aplica si hay CUALQUIER overlap entre [fecha_entrada, fecha_salida]
    y [periodo.fecha_inicio, periodo.fecha_fin].

    La lógica de overlap es:
    - El inicio del periodo debe estar antes o en la fecha de salida
    - El fin del periodo debe estar después o en la fecha de entrada

    Args:
        fecha_entrada: Fecha de check-in de la reserva
        fecha_salida: Fecha de check-out de la reserva
        hotel: HotelExcel con periodos_group definidos

    Returns:
        Lista de Periodo que tienen overlap con el rango, ordenados por fecha de inicio

    Ejemplo:
        Rango ingresado: 15-05-2025 a 20-07-2025

        Periodos del hotel:
        - P1: 01-01-2025 a 31-05-2025 (LOW)  -> SÍ (overlap: 15-05 a 31-05)
        - P2: 01-06-2025 a 30-06-2025 (MID)  -> SÍ (overlap: 01-06 a 30-06)
        - P3: 01-07-2025 a 31-08-2025 (HIGH) -> SÍ (overlap: 01-07 a 20-07)
        - P4: 01-09-2025 a 31-12-2025 (LOW)  -> NO

        Retorna: [P1, P2, P3]
    """
    periodos_aplicables = []

    for grupo in hotel.periodos_group:
        for periodo in grupo.periodos:
            # Verificar overlap: el periodo aplica si:
            # - El inicio del periodo está antes del fin de la reserva, Y
            # - El fin del periodo está después del inicio de la reserva
            if (periodo.fecha_inicio <= fecha_salida and
                periodo.fecha_fin >= fecha_entrada):
                periodos_aplicables.append(periodo)

    # Ordenar por fecha de inicio
    periodos_aplicables.sort(key=lambda p: p.fecha_inicio)

    return periodos_aplicables


def calcular_dias_por_periodo(
    fecha_entrada: date,
    fecha_salida: date,
    periodos: List[Periodo]
) -> Dict[int, int]:
    """Calcula cuántos días de la estadía corresponden a cada periodo.

    Esta función es útil para cálculos de precio prorrateado en el futuro,
    permitiendo saber exactamente cuántas noches de la reserva caen en cada periodo.

    Args:
        fecha_entrada: Fecha de check-in
        fecha_salida: Fecha de check-out
        periodos: Lista de periodos a analizar

    Returns:
        Diccionario {periodo_id: días} con la cantidad de días en cada periodo

    Ejemplo:
        Rango: 28-05-2025 a 05-06-2025 (8 noches)
        P1: 01-01 a 31-05 (LOW SEASON)  -> 3 días (28, 29, 30 mayo)
        P2: 01-06 a 30-06 (HIGH SEASON) -> 5 días (1, 2, 3, 4, 5 junio)

        Retorna: {1: 3, 2: 5}
    """
    resultado = {}

    for periodo in periodos:
        # Encontrar overlap real entre el rango de reserva y el periodo
        inicio_overlap = max(fecha_entrada, periodo.fecha_inicio)
        fin_overlap = min(fecha_salida, periodo.fecha_fin)

        # Si hay overlap válido, calcular días
        if inicio_overlap <= fin_overlap:
            dias = (fin_overlap - inicio_overlap).days + 1
            resultado[periodo.id] = dias

    return resultado
