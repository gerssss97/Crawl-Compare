from openpyxl import load_workbook
from models.hotel import *
from ExtractorDatos.utils import *
import traceback
import sys


EXCLUSIONES = [
    "season rates", "(per room)", "closing agreement",
    "rates includes", "promotion", "not included", "high speed"
]

LEYENDAS_AGREEMENT = ["closing agreement"]

def cargar_excel(path_excel, max_row=300) -> DatosExcel:
    wb = load_workbook(path_excel)
    ws = wb.active  

    hoteles: list[HotelExcel] = []
    hotel_actual: HotelExcel | None = None
    tipo_actual: TipoHabitacionExcel | None = None
    primer_habitacion = False
    
    nombre_periodo = ""
    fila_nombre_periodo = -1
    
    precio_str = None
    

    for i, row in enumerate(ws.iter_rows(values_only=True, max_row=max_row)):  # type: ignore
        if not any(row):
            continue  # fila vacía
        
        ## Logica para extraer periodos
        periodo_raw = row[1]
        if periodo_raw is not None:
            periodo_raw = str(periodo_raw)
            # Ignorar URLs y otros formatos no válidos
            if isinstance(periodo_raw, str) and ("http" in periodo_raw.lower() or "https" in periodo_raw.lower()):
                continue
            
            ## Se intentan detectar nombres de periodos tipo "low season", "high season", etc
            if contiene_season(periodo_raw):
                nombre_periodo = str(periodo_raw).strip()
                fila_nombre_periodo = i
            ## Si no hay nombre de periodo, se intenta extraer fechas 
            else:
                try:
                    ## intentamos extraer las fechas con parentesis (1May25 - 30Sep25)
                    fechas_con_parentesis = extraer_fechas_con_parentesis(periodo_raw)
                    if fechas_con_parentesis:
                        for fecha_inicio, fecha_fin in fechas_con_parentesis:
                            ## El nombre del periodo se determina por la distancia
                            ## respecto a la fila donde se encontro una leyenda con "season"
                            if fila_nombre_periodo != -1 and i - fila_nombre_periodo <= 3:
                                nombre_periodo_a_usar = nombre_periodo 
                            else:
                                nombre_periodo_a_usar = "hardoceado con parentesis"
                            periodo = construir_periodo(fecha_inicio, fecha_fin, nombre_periodo_a_usar)
                            hotel_actual.periodos.append(periodo)
                    else:
                        ## Sino, intentamos extraer fechas del tipo "New Year: 26Dec25 - 3Jan26" "Easter: 2-5Apr26"
                        ## luego mejorar la logica y hacer el chequeo previo para decidir cual metodo usar
                        resultado = extraer_fechas_sin_parentesis(periodo_raw)
                        ## Si no se pudo extraer nada, se salta
                        if not resultado:
                            continue
                    
                        nombre_periodo_extraido, fechas_sin_parentesis = resultado
                        ## Imposible extraer fechas
                        if not fechas_sin_parentesis:
                            continue
                        
                        ## se construye el periodo y se lo agrega al hotel actual
                        fecha_inicio, fecha_fin = fechas_sin_parentesis
                        if not nombre_periodo_extraido:
                            nombre_periodo_a_usar ="hardoceado sin parentesis" 
                        else:
                            nombre_periodo_a_usar = nombre_periodo_extraido
                        periodo = construir_periodo(fecha_inicio, fecha_fin, nombre_periodo_a_usar)
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

        if row[0] is None:
            continue  # sin nombre

        nombre_raw = str(row[0]).strip()
        nombre_norm = nombre_raw.lower()

        ##  Saltar exclusiones
        if any(nombre_norm.startswith(excl) for excl in EXCLUSIONES):
            continue

        
        ##  Detectar NUEVO HOTEL (empieza con "hotel" o patrón similar)
        if nombre_raw.endswith("(A)"):
            if primer_habitacion:
            # Cuando se encuentre un hotel nuevo, se agregan los periodos detectados a las habitaciones del hotel viejo
                agregar_periodos_a_habitaciones(hotel_actual)
                
            hotel_actual = HotelExcel(nombre=nombre_raw, tipos=[], habitaciones_directas=[],periodos=[])
            hoteles.append(hotel_actual)
            primer_habitacion = True
            tipo_actual = None
            continue

        ## Detectar TIPO de habitación (mayúsculas + sin precio en la fila)
        if nombre_raw.isupper() and row[2] is None:
            tipo_actual = TipoHabitacionExcel(nombre=nombre_raw, habitaciones=[])
            if hotel_actual:
                hotel_actual.tipos.append(tipo_actual)
            continue
        
        ## Logica de los PRECIOS de las habitaciones
        col_precio = obtener_valor_real(ws, i, 2)  # columna 2 = índice C en Excel
        precio = None
        
        valor_str = str(col_precio).strip().lower() if col_precio is not None else ""
        ## Lógica para detectar "closing agreement" o similares, omitiendo "habitaciones" cuyas leyendas NO esten en la lista
        if valor_str in LEYENDAS_AGREEMENT:
            precio_str = valor_str
        elif valor_str and not valor_str.replace(".", "").replace(",", "").isdigit():
            # Ejemplo: "closing" o "price TBD" → ignorar la habitación
            continue
        elif valor_str.replace(".", "").replace(",", "").isdigit():
            precio_str = None
        
        if valor_str:
            precio = valor_str
        elif precio_str:
            precio = precio_str
        
        # si no hay precio, no es una habitacion
        if not precio:
            continue  
            
        habitacion = HabitacionExcel(
            nombre=nombre_raw,
            precio=precio,
            row_idx=i,
            periodo_ids=[]  # se asignan luego
        )

        if hotel_actual:
            if tipo_actual:
                tipo_actual.habitaciones.append(habitacion)
            else:
                hotel_actual.habitaciones_directas.append(habitacion)
        ## agregar periodos a las habitaciones del ultimo hotel
    
    agregar_periodos_a_habitaciones(hotel_actual)
    return DatosExcel(hoteles=hoteles)
