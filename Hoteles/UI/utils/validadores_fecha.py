"""Validadores centralizados para fechas.

Este módulo proporciona funciones reutilizables para validar fechas
en formato DD-MM-AAAA, tanto a nivel de componentes individuales (día, mes, año)
como de fecha completa.

Ejemplo de uso:
    >>> from UI.utils.validadores_fecha import validar_dia, parsear_fecha_dd_mm_aaaa
    >>> validar_dia("15")
    True
    >>> validar_dia("32")
    False
    >>> fecha = parsear_fecha_dd_mm_aaaa("15-03-2025")
    >>> print(fecha)
    2025-03-15 00:00:00
"""

from datetime import datetime
from typing import Optional


def validar_dia(valor: str) -> bool:
    """Valida que el valor sea un día válido (1-31).

    Args:
        valor: String a validar

    Returns:
        True si es válido o vacío, False en caso contrario

    Ejemplos:
        >>> validar_dia("")
        True
        >>> validar_dia("15")
        True
        >>> validar_dia("32")
        False
        >>> validar_dia("abc")
        False
    """
    if valor == "":
        return True
    if valor.isdigit():
        n = int(valor)
        return 1 <= n <= 31
    return False


def validar_mes(valor: str) -> bool:
    """Valida que el valor sea un mes válido (1-12).

    Args:
        valor: String a validar

    Returns:
        True si es válido o vacío, False en caso contrario

    Ejemplos:
        >>> validar_mes("")
        True
        >>> validar_mes("6")
        True
        >>> validar_mes("13")
        False
        >>> validar_mes("abc")
        False
    """
    if valor == "":
        return True
    if valor.isdigit():
        n = int(valor)
        return 1 <= n <= 12
    return False


def validar_ano(valor: str) -> bool:
    """Valida que el valor sea un año válido (1-4 dígitos).

    Args:
        valor: String a validar

    Returns:
        True si es válido o vacío, False en caso contrario

    Ejemplos:
        >>> validar_ano("")
        True
        >>> validar_ano("2025")
        True
        >>> validar_ano("25")
        True
        >>> validar_ano("20255")
        False
        >>> validar_ano("abc")
        False
    """
    if valor == "":
        return True
    if valor.isdigit():
        return 1 <= len(valor) <= 4
    return False


def parsear_fecha_dd_mm_aaaa(fecha_str: str) -> Optional[datetime]:
    """Parsea una fecha en formato DD-MM-AAAA.

    Args:
        fecha_str: Fecha como string en formato DD-MM-AAAA

    Returns:
        Objeto datetime o None si el formato es inválido

    Ejemplos:
        >>> fecha = parsear_fecha_dd_mm_aaaa("15-03-2025")
        >>> print(fecha.day, fecha.month, fecha.year)
        15 3 2025
        >>> parsear_fecha_dd_mm_aaaa("32-13-2025")
        None
        >>> parsear_fecha_dd_mm_aaaa("15/03/2025")
        None
    """
    try:
        return datetime.strptime(fecha_str, "%d-%m-%Y")
    except ValueError:
        return None


def validar_fecha_formato(fecha_str: str) -> bool:
    """Valida que una fecha tenga formato DD-MM-AAAA válido.

    Args:
        fecha_str: Fecha como string

    Returns:
        True si el formato es válido, False en caso contrario

    Ejemplos:
        >>> validar_fecha_formato("15-03-2025")
        True
        >>> validar_fecha_formato("32-13-2025")
        False
        >>> validar_fecha_formato("15/03/2025")
        False
    """
    return parsear_fecha_dd_mm_aaaa(fecha_str) is not None


def validar_fecha_mayor_o_igual(fecha_str: str, fecha_referencia: datetime) -> bool:
    """Valida que una fecha sea mayor o igual a una fecha de referencia.

    Args:
        fecha_str: Fecha a validar en formato DD-MM-AAAA
        fecha_referencia: Fecha de referencia (datetime)

    Returns:
        True si la fecha es mayor o igual, False en caso contrario

    Ejemplos:
        >>> from datetime import datetime
        >>> hoy = datetime(2025, 3, 15)
        >>> validar_fecha_mayor_o_igual("20-03-2025", hoy)
        True
        >>> validar_fecha_mayor_o_igual("10-03-2025", hoy)
        False
    """
    fecha = parsear_fecha_dd_mm_aaaa(fecha_str)
    if fecha is None:
        return False
    return fecha.date() >= fecha_referencia.date()


def validar_fecha_mayor(fecha_str: str, otra_fecha_str: str) -> bool:
    """Valida que una fecha sea estrictamente mayor que otra.

    Args:
        fecha_str: Primera fecha en formato DD-MM-AAAA
        otra_fecha_str: Segunda fecha en formato DD-MM-AAAA

    Returns:
        True si fecha_str > otra_fecha_str, False en caso contrario

    Ejemplos:
        >>> validar_fecha_mayor("20-03-2025", "15-03-2025")
        True
        >>> validar_fecha_mayor("15-03-2025", "20-03-2025")
        False
        >>> validar_fecha_mayor("15-03-2025", "15-03-2025")
        False
    """
    fecha1 = parsear_fecha_dd_mm_aaaa(fecha_str)
    fecha2 = parsear_fecha_dd_mm_aaaa(otra_fecha_str)

    if fecha1 is None or fecha2 is None:
        return False

    return fecha1 > fecha2
