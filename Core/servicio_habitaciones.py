"""Servicio para unificación de habitaciones e inferencia de periodos."""

from Models.habitacion_unificada import HabitacionUnificada
from Models.hotelExcel import HabitacionExcel, HotelExcel, Periodo
from Core.modelo_gaps import Gap, GapAnalysis
from typing import List, Dict
from datetime import date, timedelta


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


def detectar_gaps(
    fecha_entrada: date,
    fecha_salida: date,
    periodos_aplicables: List[Periodo]
) -> List[Gap]:
    """Detecta períodos sin cobertura entre fechas solicitadas.

    Identifica rangos de fechas donde NO hay precio Excel disponible,
    analizando los "huecos" entre periodos aplicables.

    Lógica:
    1. Si no hay periodos → TODO el rango es gap
    2. Gap antes del primer periodo si fecha_entrada < periodo[0].fecha_inicio
    3. Gaps entre periodos consecutivos (si hay "saltos")
    4. Gap después del último periodo si fecha_salida > periodo[-1].fecha_fin

    Args:
        fecha_entrada: Inicio del rango solicitado
        fecha_salida: Fin del rango solicitado
        periodos_aplicables: Periodos que tienen overlap (ya ordenados por fecha_inicio)

    Returns:
        Lista de Gap objects representando brechas sin cobertura

    Ejemplo:
        Rango: 11/06/2025 → 11/06/2026
        Periodos: P1(01/05-30/09/2025), P2(01/05-30/09/2026)

        Gaps detectados:
        - Gap(01/10/2025, 30/04/2026)  # 7 meses sin cobertura
    """
    if not periodos_aplicables:
        # Si no hay periodos, TODO el rango es gap
        return [Gap(fecha_entrada, fecha_salida)]

    gaps = []
    periodos_ordenados = sorted(periodos_aplicables, key=lambda p: p.fecha_inicio)

    # Gap antes del primer período
    if periodos_ordenados[0].fecha_inicio > fecha_entrada:
        gaps.append(Gap(
            fecha_entrada,
            periodos_ordenados[0].fecha_inicio - timedelta(days=1)
        ))

    # Gaps entre períodos consecutivos
    for i in range(len(periodos_ordenados) - 1):
        fin_actual = periodos_ordenados[i].fecha_fin
        inicio_siguiente = periodos_ordenados[i + 1].fecha_inicio

        # Si hay brecha (más de 1 día) entre periodos → crear gap
        if inicio_siguiente > fin_actual + timedelta(days=1):
            gaps.append(Gap(
                fin_actual + timedelta(days=1),
                inicio_siguiente - timedelta(days=1)
            ))

    # Gap después del último período
    if periodos_ordenados[-1].fecha_fin < fecha_salida:
        gaps.append(Gap(
            periodos_ordenados[-1].fecha_fin + timedelta(days=1),
            fecha_salida
        ))

    return gaps


def analizar_cobertura(
    fecha_entrada: date,
    fecha_salida: date,
    hotel: HotelExcel
) -> GapAnalysis:
    """Función unificada que infiere periodos Y detecta gaps en un solo paso.

    Esta función combina:
    1. Inferencia de periodos aplicables (usando inferir_periodos_desde_fechas)
    2. Detección de gaps (usando detectar_gaps)
    3. Empaquetado en GapAnalysis para fácil acceso

    Args:
        fecha_entrada: Fecha de check-in solicitada
        fecha_salida: Fecha de check-out solicitada
        hotel: HotelExcel con periodos_group definidos

    Returns:
        GapAnalysis con periodos aplicables y gaps detectados

    Ejemplo:
        Rango: 11/06/2025 → 11/06/2026
        Excel: P1(01/05-30/09/2025), P2(01/05-30/09/2026)

        Retorna:
        GapAnalysis(
            periodos_aplicables=[P1, P2],
            gaps=[Gap(01/10/2025, 30/04/2026)],
            tiene_gaps=True
        )
    """
    # Inferir periodos con overlap
    periodos_aplicables = inferir_periodos_desde_fechas(
        fecha_entrada,
        fecha_salida,
        hotel
    )

    # Detectar gaps entre periodos
    gaps = detectar_gaps(fecha_entrada, fecha_salida, periodos_aplicables)

    # Empaquetar en GapAnalysis
    return GapAnalysis(
        fecha_entrada=fecha_entrada,
        fecha_salida=fecha_salida,
        periodos_aplicables=periodos_aplicables,
        gaps=gaps
    )
