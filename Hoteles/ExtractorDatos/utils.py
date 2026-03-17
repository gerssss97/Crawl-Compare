import calendar
from datetime import date
import re
from typing import Optional
from Models.hotelExcel import Periodo, HotelExcel, PeriodoGroup
from openpyxl.utils import range_boundaries



def contiene_season(texto: str) -> bool:
    if not isinstance(texto, str):
        return False
    return 'season' in texto.lower()

def contiene_special_dates(texto: str) -> bool:
    if not isinstance(texto, str):
        return False
    return 'special dates' in texto.lower()

def parece_periodo(texto) -> bool:
    """
    Determina si un texto parece ser un periodo válido para procesar.
    Retorna True si contiene 'season', fechas entre paréntesis, o formato 'Nombre: fecha - fecha'.
    """
    if not texto:
        return False

    texto_str = str(texto).strip()

    # Ignorar URLs
    if "http" in texto_str.lower() or "https" in texto_str.lower():
        return False

    # Si contiene "season", es un periodo
    if contiene_season(texto_str):
        return True
    
    if contiene_special_dates(texto_str):
        return True

    # Si contiene paréntesis con contenido, probablemente sea un periodo
    if '(' in texto_str and ')' in texto_str:
        return True

    # Si tiene formato "Algo: fecha - fecha" con meses abreviados
    # Buscar patrones como "26Dec25", "3Jan26", etc.
    patron_fecha = r'\d{1,2}[A-Za-z]{3}\d{2}'
    if re.search(patron_fecha, texto_str):
        return True

    return False


def parsear_string_a_fecha(token: str) -> Optional[date]:
    
    """
    Parsea un token como '1May25', '1 May 2025', '01 May 25' etc.
    Devuelve una fecha o nada si no se pudo parsear.
    """
    mes_a_numero = {}
# populate mapping with english month names and abbreviations (case-insensitive)
    for i in range(1, 13):
        mes_a_numero[calendar.month_name[i].lower()] = i
        mes_a_numero[calendar.month_abbr[i].lower()] = i

    s = token.strip()
    if not s:
        return None

    # Remueve sufijos como (1st, 2nd, 3rd, 4th...) . re.sub reemplaza todas las ocurrencias.
    # (?P<d>...) — define un grupo de captura con nombre. En este caso, el nombre del grupo es "d".
    s = re.sub(r'(?P<d>\d+)(?:st|nd|rd|th)\b', r'\g<d>', s, flags=re.IGNORECASE)

    # Intenta extraer dia, mes, año con regex
    m = re.match(r'^\s*(\d{1,2})\s*([A-Za-z]{3,})\.?\s*(\d{2,4})?\s*$', s)
    if not m:
        # tambien se aceptan expresiones del tipo mes - dia - año 'May 1 25' or 'May 1,25'
        m2 = re.match(r'^\s*([A-Za-z]{3,})\.?\s*(\d{1,2})(?:[,\s]+(\d{2,4}))?\s*$', s)
        if m2:
            mes_str = m2.group(1).lower()
            dia = int(m2.group(2))
            year_token = m2.group(3)
        else:
            return None
    else:
        dia = int(m.group(1))
        mes_str = m.group(2).lower()
        year_token = m.group(3)

    month = mes_a_numero.get(mes_str)
    if not month:
        return None

    if year_token:
        y = int(year_token)
        if y < 100:
            # Transforma un año de 2 dígitos en 4 dígitos (asumiendo siglo 2000) 
            y = 2000 + y

    try:
        return date(y, month, dia)
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
        split = re.split(r'\s*(?:-|–|—|to|\/)\s*', part, maxsplit=1, flags=re.IGNORECASE)

        if len(split) == 2:
            parte_izq, parte_der = split[0].strip(), split[1].strip()

            def _extract_year(tok: str) -> Optional[int]:
                m = re.search(r'(\d{2,4})\b', tok)
                if not m:
                    return None
                y = int(m.group(1))
                return 2000 + y if y < 100 else y
            
            fecha_izq = parsear_string_a_fecha(parte_izq)
            fecha_der = parsear_string_a_fecha(parte_der)
            if fecha_izq and fecha_der:
                results.append((fecha_izq, fecha_der))
            else:
                raise ValueError(f"No se pudo parsear alguna de las fechas en el rango: {part}")  
        else:
            # single token inside parentheses -> parse as single date or maybe as single range-like token
            token = split[0].strip()
            # If token contains a dash inside (but splitting failed because of weird chars), try generic split
            if re.search(r'[-–—]', token) and len(re.split(r'\s*(?:-|–|—)\s*', token, maxsplit=1)) == 2:
                parte_izq, parte_der = re.split(r'\s*(?:-|–|—)\s*', token, maxsplit=1)
                fecha_izq = parsear_string_a_fecha(parte_izq)
                fecha_der = parsear_string_a_fecha(parte_der)
                if fecha_izq and fecha_der:
                    results.append((fecha_izq, fecha_der))
                
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
    print(f"[DEBUG] Procesando texto: {text}")
    if not text:
        return []

    # Dividir la cadena en nombre y rango de fechas
    partes = text.split(":", 1)
    print(f"[DEBUG] Partes después del split: {partes}")
    if len(partes) != 2:
        return []  

    nombre = partes[0].strip()
    rango_fechas = partes[1].strip()
    print(f"[DEBUG] Nombre: {nombre}")
    print(f"[DEBUG] Rango de fechas: {rango_fechas}")
    # Separar las fechas
    split = re.split(r'\s*(?:-|–|—|to|\/)\s*', rango_fechas, maxsplit=1, flags=re.IGNORECASE)
    print(f"[DEBUG] Split de fechas: {split}")
    if len(split) != 2:
        return []  # No hay separador de fechas

    parte_izq, parte_der = split[0].strip(), split[1].strip()
    print(f"[DEBUG] Fecha izquierda: {parte_izq}")
    print(f"[DEBUG] Fecha derecha: {parte_der}")

    ## chequeo especial: si la parte izquierda no tiene año, intentar extraerlo de la parte derecha
    if len(parte_izq) <= 2:
        match = re.search(r'^\s*(?:(\d{1,2}))\s*([A-Za-z]{3,})\.?\s*(\d{2,4})?\s*', parte_der)
        if match:
            mes = match.group(2) if match.group(2) else ""
            anio = match.group(3) if match.group(3) else ""
            parte_izq += mes + anio
            print(f"[DEBUG] Fecha izquierda modificada (añadido año): {parte_izq}")
        else:
            print(f"[DEBUG] No se encontró patrón para extraer mes y año de la parte derecha")
        
    # Parsear las fechas
    fecha_izq = parsear_string_a_fecha(parte_izq)
    fecha_der = parsear_string_a_fecha(parte_der)

    if fecha_izq and fecha_der:
        return [nombre,(fecha_izq, fecha_der)]
    else:
        print(f"[WARNING] No se pudieron parsear las fechas para {nombre}")
        return [nombre]  # No se pudieron parsear las fechas pero devolvemos el nombre


def obtener_valor_real(ws, fila, col):
    """Devuelve el valor real de una celda, incluso si pertenece a un merge."""
    cell = ws.cell(row=fila + 1, column=col + 1)  # +1 porque enumerate empieza en 0
    for merged_range in ws.merged_cells.ranges:
        min_col, min_row, max_col, max_row = range_boundaries(str(merged_range))
        if min_row <= cell.row <= max_row and min_col <= cell.column <= max_col:
            # La celda pertenece a un merge → usar la principal (superior izquierda)
            top_left = ws.cell(row=min_row, column=min_col)
            return top_left.value
    return cell.value

def agregar_nombre_group(hotel: HotelExcel, nombre: str):
    grupo = PeriodoGroup(nombre = nombre, periodos= [] )
    hotel.periodos_group.append(grupo)
    return
    


def construir_periodo(fecha_inicio : date, fecha_fin : date , nombre: Optional[str] = None) -> Periodo:
    periodo = Periodo.crear(fecha_inicio, fecha_fin, nombre)
    return periodo

def agregar_periodos_a_habitaciones(hotel : HotelExcel):
    if not hotel.tipos :
        for habitacion in hotel.habitaciones_directas:
            for periodo in hotel.periodos:
                habitacion.periodo_ids.append(periodo.id)    
    else:
        for tipo in hotel.tipos:
            for habitacion in tipo.habitaciones:
                for periodo in hotel.periodos:
                    habitacion.periodo_ids.append(periodo.id)
    return
