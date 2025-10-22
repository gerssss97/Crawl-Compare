from openpyxl import load_workbook
from models.hotel import *
from ExtractorDatos.utils import *
import traceback
import sys

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
    
    
    for i, row in enumerate(ws.iter_rows(values_only=True, max_row=max_row)):  # type: ignore
        if not any(row):
            continue  # fila vacía

        if row[0] is None:
            continue  # sin nombre
        
        ## Logica para extraer periodos
        periodo_raw = row[1]
        nombre_periodo = ""
        if periodo_raw is not None:
            # Ignorar URLs y otros formatos no válidos
            if isinstance(periodo_raw, str) and ("http" in periodo_raw.lower() or "https" in periodo_raw.lower()):
                print(f"[INFO] Fila {i}: Ignorando URL en columna de períodos: {periodo_raw[:50]}...")
                continue
            
            ## Se intentan detectar nombres de periodos tipo "low season", "high season", etc
            if contiene_season(periodo_raw):
                nombre_periodo = str(periodo_raw).strip()
                print(f"[DEBUG] Fila {i}: Periodo detectado: {nombre_periodo}")
            ## Si no hay nombre de periodo, se intenta extraer fechas 
            else:
                try:
                    ## intentamos extraer las fechas con parentesis (1May25 - 30Sep25)
                    print(f"[DEBUG] Fila {i}: Procesando dato: {periodo_raw}")
                    fechas_con_parentesis = extraer_fechas_con_parentesis(periodo_raw)
                    print(f"[DEBUG] Fila {i}: Fechas con paréntesis encontradas: {fechas_con_parentesis}")
                    if fechas_con_parentesis:
                        for fecha_inicio, fecha_fin in fechas_con_parentesis:
                            if nombre_periodo == "": nombre_periodo = "hardoceado con parentesis"
                            print(f"[DEBUG] Fila {i}: fecha extraida {periodo_raw}")
                            periodo = construir_periodo(fecha_inicio, fecha_fin, nombre_periodo)
                            hotel_actual.periodos.append(periodo)
                    else:
                        ## Sino, intentamos extraer fechas del tipo "New Year: 26Dec25 - 3Jan26" "Easter: 2-5Apr26"
                        ## luego mejorar la logica y hacer el chequeo previo para decidir cual metodo usar
                        print(f"[DEBUG] Fila {i}: Intentando extraer fechas sin paréntesis")
                        resultado = extraer_fechas_sin_parentesis(str(periodo_raw))
                        if not resultado:
                            print(f"[DEBUG] Fila {i}: No se encontraron fechas en: {periodo_raw}")
                            continue
                    
                        nombre_periodo, fechas_sin_parentesis = resultado
                        if not fechas_sin_parentesis:
                            print(f"[DEBUG] Fila {i}: No se encontraron fechas válidas en: {periodo_raw}")
                            continue
                        
                        ## se construye el periodo y se lo agrega al hotel actual
                        print(f"[DEBUG] Fila {i}: Fechas con paréntesis encontradas: {fechas_con_parentesis}")
                        fecha_inicio, fecha_fin = fechas_sin_parentesis[1]
                        if nombre_periodo == "": nombre_periodo ="hardoceado sin parentesis"
                        periodo = construir_periodo(fecha_inicio, fecha_fin, nombre_periodo)
                        hotel_actual.periodos.append(periodo)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    print(f"[ERROR] Fila {i}:")
                    print(f"  - Dato original: {periodo_raw}")
                    print(f"  - Tipo de error: {type(e).__name__}")
                    print(f"  - Mensaje: {str(e)}")
                    print(f"  - Hotel actual: {hotel_actual.nombre if hotel_actual else 'None'}")
                    print("  - Traceback:")
                    for filename, lineno, funcname, line in traceback.extract_tb(exc_traceback):
                        print(f"    Archivo: {filename}")
                        print(f"    Línea: {lineno}")
                        print(f"    Función: {funcname}")
                        if line:
                            print(f"    Código: {line}")
                    print("  -------------------")

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
