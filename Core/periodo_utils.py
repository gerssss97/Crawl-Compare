from Models.hotelExcel import HotelExcel, HabitacionExcel
from typing import Dict, List
from datetime import date


def formatear_periodos_habitacion(hotel: HotelExcel, habitacion: HabitacionExcel) -> str:
    """
    Formatea los periodos de una habitación agrupados por nombre de grupo.

    Args:
        hotel: Objeto HotelExcel que contiene los grupos de periodos
        habitacion: Objeto HabitacionExcel con los periodo_ids asignados

    Returns:
        String formateado con los periodos agrupados por nombre, o mensaje de advertencia si no hay periodos

    Ejemplo de retorno:
        High Season:
          • 01/05/2025 - 30/09/2025
          • 12/12/2025 - 27/12/2025

        Low Season:
          • 01/10/2025 - 11/12/2025
    """
    if not habitacion.periodo_ids:
        return "⚠️ ADVERTENCIA: Sin periodos asignados"

    # Agrupar los periodos por nombre de grupo
    grupos_periodos: Dict[str, List[str]] = {}

    for pid in habitacion.periodo_ids:
        periodo = hotel.periodo_por_id(pid)
        if periodo:
            # Buscar a qué grupo pertenece este periodo
            nombre_grupo = None
            for grupo in hotel.periodos_group:
                if periodo in grupo.periodos:
                    nombre_grupo = grupo.nombre
                    break

            if nombre_grupo:
                # Formatear la fecha
                fecha_formateada = formatear_rango_fecha(periodo.fecha_inicio, periodo.fecha_fin)

                # Agregar al grupo correspondiente
                if nombre_grupo not in grupos_periodos:
                    grupos_periodos[nombre_grupo] = []
                grupos_periodos[nombre_grupo].append(fecha_formateada)

    if not grupos_periodos:
        return "⚠️ ADVERTENCIA: Sin periodos asignados"

    # Construir el string de salida
    resultado = []
    for nombre_grupo, fechas in grupos_periodos.items():
        resultado.append(f"{nombre_grupo}:")
        for fecha in fechas:
            resultado.append(f"  • {fecha}")
        resultado.append("")  # Línea en blanco entre grupos

    return "\n".join(resultado).rstrip()


def formatear_rango_fecha(fecha_inicio: date, fecha_fin: date) -> str:
    """
    Formatea un rango de fechas en formato DD/MM/YYYY - DD/MM/YYYY

    Args:
        fecha_inicio: Fecha de inicio del periodo
        fecha_fin: Fecha de fin del periodo

    Returns:
        String con el rango formateado
    """
    inicio_str = fecha_inicio.strftime("%d/%m/%Y")
    fin_str = fecha_fin.strftime("%d/%m/%Y")
    return f"{inicio_str} - {fin_str}"