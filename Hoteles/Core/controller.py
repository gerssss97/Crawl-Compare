from .gestor_datos import *
from typing import Optional
from Core.email_templates import DEFAULT_EMAIL_TEMPLATE


class GestorService:
    """Singleton recargable del GestorDatos.

    Reemplaza la instancia global `gestor` para permitir cambiar el Excel
    en runtime. Si la recarga falla, la instancia previa queda intacta
    (la asignación a `_instance` sólo ocurre si el constructor no lanza).

    Quien necesite el gestor debe llamar a ``GestorService.get()`` en el
    momento de uso, NO importar la instancia (eso traería stale references).
    """

    _instance: Optional[GestorDatos] = None
    _current_path: Optional[str] = None

    @classmethod
    def cargar(cls, path: str) -> GestorDatos:
        nuevo = GestorDatos(path)
        cls._instance = nuevo
        cls._current_path = path
        return nuevo

    @classmethod
    def get(cls) -> Optional[GestorDatos]:
        return cls._instance

    @classmethod
    def get_current_path(cls) -> Optional[str]:
        return cls._current_path

    @classmethod
    def esta_cargado(cls) -> bool:
        return cls._instance is not None

    @classmethod
    def reset(cls) -> None:
        cls._instance = None
        cls._current_path = None


# Funciones legacy — defensivas: devuelven [] cuando no hay Excel cargado.
def dar_hoteles_excel():
    g = GestorService.get()
    if g is None:
        return []
    return g.hoteles_excel_get

def dar_habitaciones_excel(hotelExcel: HotelExcel, tipo):
    g = GestorService.get()
    if g is None:
        return []
    return g.habitaciones_excel_get(hotelExcel, tipo)

def dar_tipos_habitacion_excel(HotelExcel: HotelExcel):
    g = GestorService.get()
    if g is None:
        return []
    return g.tipos_habitaciones_excel_get(HotelExcel)

## devuelve true si la diferencia es mayor o igual a 1
async def comparar_habitaciones(habitacion_excel: HabitacionExcel, precio_hab_excel):
    g = GestorService.get()
    if g is None:
        raise RuntimeError("No hay archivo Excel cargado.")
    await g.coincidir_excel_web(habitacion_excel) #busca la mejor coincidencia con hab web

    precio_web = g.mejor_habitacion_web_get.combos[0].precio  # type: ignore
    diferencia = abs(float(precio_hab_excel) - precio_web) # type: ignore
    print(f"Precio Excel: {precio_hab_excel} - Precio Web: {precio_web} - Diferencia: {diferencia}")
    if diferencia>=1:
        return True
    else:
        return False


def dar_habitacion_web():
    g = GestorService.get()
    if g is None:
        return None
    return g.mejor_habitacion_web_get

def dar_mensaje():
    g = GestorService.get()
    if g is None:
        return None
    return g.mensaje_get

async def dar_hotel_web(hotel_nombre: str, fecha_ingreso, fecha_egreso, adultos, niños, edades_ninos: list = None, force_fresh=False, use_pickle=True, force_pickle=False, on_scrape_step=None):
    """Obtiene datos del hotel web.

    Args:
        fecha_ingreso: Fecha entrada DD-MM-YYYY
        fecha_egreso: Fecha salida DD-MM-YYYY
        adultos: Número de adultos
        niños: Número de niños
        force_fresh: Si True, ignora TODO caché y hace scraping fresco
        use_pickle: Si False, ignora pickle pero usa caché en memoria
        force_pickle: Si True, USA SIEMPRE el pickle (para testing, ignora fechas)
        on_scrape_step: Callback opcional(step: str) para reportar etapas del scraping

    Returns:
        HotelWeb con datos scrapeados

    Raises:
        ValueError: Si no se pueden obtener datos válidos
        FileNotFoundError: Si force_pickle=True pero no existe el archivo pickle
    """
    g = GestorService.get()
    if g is None:
        raise RuntimeError("No hay archivo Excel cargado.")
    hotel = await g.obtener_hotel_web(hotel_nombre, fecha_ingreso, fecha_egreso, adultos, niños, edades_ninos=edades_ninos or [], force_fresh=force_fresh, use_pickle=use_pickle, force_pickle=force_pickle, on_scrape_step=on_scrape_step)

    if hotel is None or not hotel.habitacion:
        raise ValueError("No se pudieron obtener datos válidos del hotel web")
    return hotel

def _renderizar_template(template: str, hotel: str, resultado, firma: str) -> str:
    import re

    TAG_FOR = "{% for periodo %}"
    TAG_END = "{% end %}"

    partes = template.split(TAG_FOR)
    antes = partes[0]
    if len(partes) == 1:
        bloque_raw = ""
        despues = ""
    else:
        resto = partes[1].split(TAG_END)
        bloque_raw = resto[0]
        despues = TAG_END.join(resto[1:])

    ctx_global = {
        "hotel": hotel,
        "habitacion_excel": resultado.habitacion_excel_nombre,
        "habitacion_web": resultado.habitacion_web_matcheada.nombre,
        "firma": firma,
    }

    def _sub_global(m):
        return ctx_global.get(m.group(1), m.group(0))

    texto_antes   = re.sub(r"\{(\w+)\}", _sub_global, antes)
    texto_despues = re.sub(r"\{(\w+)\}", _sub_global, despues)

    bloques = []
    for rp in resultado.periodos:
        p = rp.periodo
        fecha_inicio_b = rp.fecha_inicio_real.strftime("%d/%m/%Y") if rp.fecha_inicio_real else p.fecha_inicio.strftime("%d/%m/%Y")
        fecha_fin_b    = rp.fecha_fin_real.strftime("%d/%m/%Y")    if rp.fecha_fin_real    else p.fecha_fin.strftime("%d/%m/%Y")

        if isinstance(rp.precio_excel, (int, float)):
            precio_excel_fmt = f"${rp.precio_excel:.2f}"
            diferencia_fmt   = f"${rp.diferencia:.2f}"
        else:
            precio_excel_fmt = str(rp.precio_excel)
            diferencia_fmt   = "N/A"

        if rp.precio_excel == "Error":
            estado = "ERROR"
        else:
            estado = "OK" if rp.coincide else "DIFF"

        ctx_periodo = {
            "periodo_id":            str(p.id),
            "fecha_inicio_periodo":  p.fecha_inicio.strftime("%d/%m/%Y"),
            "fecha_fin_periodo":     p.fecha_fin.strftime("%d/%m/%Y"),
            "fecha_inicio_busqueda": fecha_inicio_b,
            "fecha_fin_busqueda":    fecha_fin_b,
            "precio_excel":          precio_excel_fmt,
            "precio_web":            f"${rp.precio_web:.2f}",
            "diferencia":            diferencia_fmt,
            "estado":                estado,
        }

        def _sub_periodo(m, ctx=ctx_periodo):
            return ctx.get(m.group(1), m.group(0))

        bloques.append(re.sub(r"\{(\w+)\}", _sub_periodo, bloque_raw))

    return texto_antes + "".join(bloques) + texto_despues


def generar_texto_email_multiperiodo(hotel, resultado_multiperiodo, template: str | None = None, firma: str = "Germán Lucero"):
    t = template if template is not None else DEFAULT_EMAIL_TEMPLATE
    return _renderizar_template(t, hotel, resultado_multiperiodo, firma)


