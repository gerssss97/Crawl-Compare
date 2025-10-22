import calendar
from datetime import date
import re
from typing import Optional

def contiene_season(text: str) -> bool:
    return 'season' in text.lower()

_month_name_to_num = {}
# populate mapping with english month names and abbreviations (case-insensitive)
for i in range(1, 13):
    _month_name_to_num[calendar.month_name[i].lower()] = i
    _month_name_to_num[calendar.month_abbr[i].lower()] = i

def parsear_string_a_fecha(token: str) -> Optional[date]:
    """
    Parsea un token como '1May25', '1 May 2025', '01 May 25' etc.
    Devuelve una fecha o nada si no se pudo parsear.
    """
    s = token.strip()
    if not s:
        return None

    # Remueve sufijos como (1st, 2nd, 3rd, 4th...) . re.sub reemplaza todas las ocurrencias.
    # (?P<d>...) — define un grupo de captura con nombre. En este caso, el nombre del grupo es "d".
    s = re.sub(r'(?P<d>\d+)(?:st|nd|rd|th)\b', r'\g<d>', s, flags=re.IGNORECASE)

    # Try to extract day, month, year with regex
    m = re.match(r'^\s*(\d{1,2})\s*([A-Za-z]{3,})\.?\s*(\d{2,4})?\s*$', s)
    if not m:
        # tambien se aceptan expresiones del tipo mes - dia - año 'May 1 25' or 'May 1,25'
        m2 = re.match(r'^\s*([A-Za-z]{3,})\.?\s*(\d{1,2})(?:[,\s]+(\d{2,4}))?\s*$', s)
        if m2:
            month_str = m2.group(1).lower()
            day = int(m2.group(2))
            year_token = m2.group(3)
        else:
            return None
    else:
        day = int(m.group(1))
        month_str = m.group(2).lower()
        year_token = m.group(3)

    month = _month_name_to_num.get(month_str)
    if not month:
        return None

    if year_token:
        y = int(year_token)
        if y < 100:
            # Transforma un año de 2 dígitos en 4 dígitos (asumiendo siglo 2000) 
            y = 2000 + y

    try:
        return date(y, month, day)
    except Exception:
        return None

def extraer_fechas_con_parentesis(text: str) -> list[tuple[date, date]]:
    """
    Extrae uno o varios rangos de fechas que aparecen entre paréntesis en la cadena `text`.
    Soporta entradas como:
      "(1May25 - 30Sep25) (1May26 - 30Sep26)"
      "(1May25 - 30Sep25)"
      "(1May25)"
      "(May 1 25 - Sep 30 25)"
    Devuelve una lista de tuplas (fecha_inicio: date, fecha_fin: date).
    Si el paréntesis contiene una sola fecha, se devuelve (fecha, fecha).
    Si alguna fecha no puede parsearse, esa entrada se omite.

    Ejemplo:
      parse_parenthesized_date_ranges("(1May25 - 30Sep25) (1May26 - 30Sep26)")
      -> [(date(2025,5,1), date(2025,9,30)), (date(2026,5,1), date(2026,9,30))]
    """
    if not text:
        return []
    
    results: list[tuple[date, date]] = []
    # extraer contenidos entre paréntesis
    parts = re.findall(r'\(([^)]*)\)', text)
    for part in parts:
        part = part.strip()
        if not part:
            continue

        # separar por guion/ndash/emdash/to (solo el primer guion, en caso de que haya más)
        # permitimos '-' '–' '—' y la palabra 'to'
        # obtenemos fecha inicio y fecha fin separadas
        split = re.split(r'\s*(?:-|–|—|to)\s*', part, maxsplit=1, flags=re.IGNORECASE)

        if len(split) == 2:
            left_token, right_token = split[0].strip(), split[1].strip()

            def _extract_year(tok: str) -> Optional[int]:
                m = re.search(r'(\d{2,4})\b', tok)
                if not m:
                    return None
                y = int(m.group(1))
                return 2000 + y if y < 100 else y
            
            left_dt = parsear_string_a_fecha(left_token)
            right_dt = parsear_string_a_fecha(right_token)
            if left_dt and right_dt:
                results.append((left_dt, right_dt))
            else:
                raise ValueError(f"No se pudo parsear alguna de las fechas en el rango: {part}")  
        else:
            # single token inside parentheses -> parse as single date or maybe as single range-like token
            token = split[0].strip()
            # If token contains a dash inside (but splitting failed because of weird chars), try generic split
            if re.search(r'[-–—]', token) and len(re.split(r'\s*(?:-|–|—)\s*', token, maxsplit=1)) == 2:
                left_token, right_token = re.split(r'\s*(?:-|–|—)\s*', token, maxsplit=1)
                left_dt = parsear_string_a_fecha(left_token)
                right_dt = parsear_string_a_fecha(right_token)
                if left_dt and right_dt:
                    results.append((left_dt, right_dt))
                    
    return results

def extraer_fechas_sin_parentesis(text: str) -> list[tuple[date, date]]:
    """
    Extrae rangos de fechas del formato "Nombre: fecha_inicio - fecha_fin".
    Ejemplos:
        "New Year: 26Dec25 - 3Jan26"
        "Easter: 2-5Apr26"
    Devuelve una lista de tuplas (fecha_inicio: date, fecha_fin: date).
    Si no se puede parsear alguna fecha, se omite el rango completo.
    """
    if not text:
        return []

    # Dividir la cadena en nombre y rango de fechas
    partes = text.split(":", 1)
    if len(partes) != 2:
        return []  # No hay separador ":"

    nombre = partes[0].strip()
    rango_fechas = partes[1].strip()

    # Separar las fechas
    split = re.split(r'\s*(?:-|–|—|to)\s*', rango_fechas, maxsplit=1, flags=re.IGNORECASE)
    if len(split) != 2:
        return []  # No hay separador de fechas

    left_token, right_token = split[0].strip(), split[1].strip()

    # Parsear las fechas
    left_dt = parsear_string_a_fecha(left_token)
    right_dt = parsear_string_a_fecha(right_token)

    if left_dt and right_dt:
        return [nombre,(left_dt, right_dt)]
    else:
        return [nombre]  # No se pudieron parsear las fechas pero devolvemos el nombre

def construir_periodo(fecha):
    pass