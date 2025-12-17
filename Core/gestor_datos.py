from ExtractorDatos.extractor import *
from ScrawlingChinese.crawler import *
from Models.hotelExcel import *
from Models.hotelWeb import *
from Core.comparador import *
import pickle
from datetime import datetime
from pathlib import Path

class GestorDatos:
    # Path absoluto al directorio raíz del proyecto
    _PROJECT_ROOT = Path(__file__).parent.parent
    _CACHE_FILE = _PROJECT_ROOT / "hotel_guardado_nuevos.pkl"

    def __init__(self,path_excel):
        self.__path = path_excel
        self.__datos_excel = cargar_excel(self.__path) 
        self.__hotel_web : Optional[HotelWeb] = None
        self.__habitaciones_web : Optional[List[HabitacionWeb]] = None
        self.mejor_habitacion_web : HabitacionWeb | None

        self.__last_fecha_ingreso = None
        self.__last_fecha_egreso = None
        self.__last_adultos = None
        self.__last_niños = None
        self.mensaje_match = None
    
    async def coincidir_excel_web (self, habitacion_excel: HabitacionExcel):
        if not self.__habitaciones_web:
            raise ValueError("No hay datos de habitaciones web cargados al momento de COINCIDIR con el excel")
        self.mejor_habitacion_web, self.mensaje_match = obtener_mejor_match_con_breakfast(habitacion_excel, self.__habitaciones_web)
        print("MEJOR HABITACION WEB ",self.mejor_habitacion_web)
        if self.mejor_habitacion_web is None:
            raise ValueError(f"[ERROR] No se encontró una coincidencia para el combo", habitacion_excel)
        return 

    async def obtener_hotel_web(self, fecha_ingreso, fecha_egreso, adultos, niños, force_fresh=False, use_pickle=True, force_pickle=False):
        """Obtiene datos del hotel web, con control granular de caché.

        Args:
            fecha_ingreso: Fecha entrada DD-MM-YYYY
            fecha_egreso: Fecha salida DD-MM-YYYY
            adultos: Número de adultos
            niños: Número de niños
            force_fresh: Si True, ignora TODO caché (memoria Y archivo) y hace scraping fresco
            use_pickle: Si False, ignora pickle pero usa caché en memoria (útil para multi-periodo)
            force_pickle: Si True, USA SIEMPRE el pickle (para testing, ignora fechas)

        Returns:
            HotelWeb con datos scrapeados
        """
        print(f"[DEBUG] obtener_hotel_web llamado con: force_fresh={force_fresh}, use_pickle={use_pickle}, force_pickle={force_pickle}")

        # MODO TESTING: Si force_pickle=True, cargar pickle SIEMPRE (ignora todo lo demás)
        if force_pickle:
            if self._CACHE_FILE.exists():
                with open(self._CACHE_FILE, "rb") as f:
                    print(f"[TESTING MODE] Cargando pickle forzadamente desde {self._CACHE_FILE}")
                    self.__hotel_web = pickle.load(f)
                    self.__habitaciones_web = self.__hotel_web.habitacion
                    return self.__hotel_web
            else:
                raise FileNotFoundError(f"force_pickle=True pero no existe {self._CACHE_FILE}")

        # Check caché en memoria (solo si no forzamos fresco)
        if not force_fresh:
            if (self.__last_fecha_ingreso == fecha_ingreso and
                self.__last_fecha_egreso == fecha_egreso and
                self.__last_adultos == adultos and
                self.__last_niños == niños):
                print("Usando datos de hotel web en caché de memoria.")
                return self.__hotel_web

        # Check caché en archivo (solo si use_pickle=True, no forzamos fresco Y existe archivo)
        if use_pickle and not force_fresh and self._CACHE_FILE.exists():
            with open(self._CACHE_FILE, "rb") as f:
                print(f"Usando datos de hotel web desde {self._CACHE_FILE}")
                self.__hotel_web = pickle.load(f)
                self.__habitaciones_web = self.__hotel_web.habitacion
                # Actualizar parámetros de caché en memoria
                self.__last_fecha_ingreso = fecha_ingreso
                self.__last_fecha_egreso = fecha_egreso
                self.__last_adultos = adultos
                self.__last_niños = niños
                return self.__hotel_web

        # Realizar scraping fresco
        print(f"Realizando scraping fresco para {fecha_ingreso} a {fecha_egreso}...")
        self.__last_fecha_ingreso = fecha_ingreso
        self.__last_fecha_egreso = fecha_egreso
        self.__last_adultos = adultos
        self.__last_niños = niños

        fecha_ingreso_iso = datetime.strptime(fecha_ingreso, "%d-%m-%Y").strftime("%Y-%m-%d")
        fecha_egreso_iso = datetime.strptime(fecha_egreso, "%d-%m-%Y").strftime("%Y-%m-%d")

        self.__hotel_web = await crawl_alvear(fecha_ingreso_iso, fecha_egreso_iso, adultos, niños)
        self.__habitaciones_web = self.__hotel_web.habitacion

        # Guardar en archivo pickle (solo si use_pickle=True)
        if use_pickle:
            with open(self._CACHE_FILE, "wb") as f:
                pickle.dump(self.__hotel_web, f)
                print(f"Hotel guardado en {self._CACHE_FILE}")

        return self.__hotel_web    
           
    @property
    def hoteles_excel_get(self)-> List[HotelExcel]:
        return self.__datos_excel.hoteles

    @property
    def mejor_habitacion_web_get(self)-> HabitacionWeb | None:
        return self.mejor_habitacion_web   
    
    @property
    def mensaje_get(self)-> str | None:
        return self.mensaje_match
      
