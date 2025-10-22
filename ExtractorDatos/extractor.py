from openpyxl import load_workbook
from models.hotel import *
from ExtractorDatos.utils import *

EXCLUSIONES = [
    "season rates", "(per room)", "closing agreement",
    "rates includes", "promotion", "not included", "high speed"
]

def cargar_excel(path_excel, max_row=200) -> DatosExcel:
    wb = load_workbook(path_excel)
    ws = wb.active  

    hoteles: list[HotelExcel] = []
    hotel_actual: HotelExcel | None = None
    tipo_actual: TipoHabitacionExcel | None = None
    periodo = Periodo | None = None
    for i, row in enumerate(ws.iter_rows(values_only=True, max_row=max_row)):  # type: ignore
        if not any(row):
            continue  # fila vacía

        if row[0] is None:
            continue  # sin nombre
        periodo_raw = row[1]
        if periodo_raw is not None:
            if contiene_season(periodo_raw):
                periodo.nombre = str(row[1]).strip()
            else:
                try:
                    fechas_parentesis = extraer_fechas_con_parentesis()
                    if fechas_parentesis:
                        for fecha in fechas:
                            periodo = construir_periodo(fecha)
                            nombre_periodo = 
                            hotel_actual.periodos.append(periodo)
                    else:
                        nombre_periodo, fechas_sin_parentesis = extraer_fechas_sin_parentesis(str(row[1]))
                        if fechas_sin_parentesis:
                            nombre_periodo = fechas_sin_parentesis[0]
                            fechas = fechas_sin_parentesis[1]
                            periodo = construir_periodo(fechas)
                            periodo.nombre = nombre_periodo
                            hotel_actual.periodos.append(periodo)
                except Exception as e:
                    print(f"Error al identificar fechas en fila {i+1}: {e}")

        nombre_raw = str(row[0]).strip()
        nombre_norm = nombre_raw.lower()

        # 🔹 Saltar exclusiones
        if any(nombre_norm.startswith(excl) for excl in EXCLUSIONES):
            continue

        # 🔹 Detectar nuevo hotel (empieza con "hotel" o patrón similar)
        if nombre_raw.endswith("(A)"):
            hotel_actual = HotelExcel(nombre=nombre_raw, tipos=[], habitaciones_directas=[])
            hoteles.append(hotel_actual)
            tipo_actual = None
            continue

        # 🔹 Detectar tipo de habitación (mayúsculas + sin precio en la fila)
        if nombre_raw.isupper() and row[2] is None:
            tipo_actual = TipoHabitacionExcel(nombre=nombre_raw, habitaciones=[])
            if hotel_actual:
                hotel_actual.tipos.append(tipo_actual)
            continue

        # 🔹 Habitaciones (con o sin tipo)
        col_precio = row[2]
        precio = None
        if col_precio is not None and str(col_precio).strip() != "":
            precio = str(col_precio)
            
        habitacion = HabitacionExcel(
            nombre=nombre_raw,
            precio=precio,
            row_idx=i
        )

        if hotel_actual:
            if tipo_actual:
                tipo_actual.habitaciones.append(habitacion)
            else:
                hotel_actual.habitaciones_directas.append(habitacion)
    
    return DatosExcel(hoteles=hoteles)
