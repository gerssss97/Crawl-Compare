from ExtractorDatos.extractor import *
from ScrawlingChinese.crawler import *
from Models.hotelExcel import *
from Models.hotelWeb import *
from Core.comparador import *
import pickle
import os
from datetime import datetime

class GestorDatos:
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

    async def obtener_hotel_web(self, fecha_ingreso, fecha_egreso, adultos, niños):
        if (self.__last_fecha_ingreso == fecha_ingreso and
            self.__last_fecha_egreso == fecha_egreso and
            self.__last_adultos == adultos and
            self.__last_niños == niños):
            print("Usando datos de hotel web en caché.")

        if os.path.exists("hotel_guardado.pkl"):
            with open("hotel_guardado.pkl", "rb") as f:
                print("Usando datos de hotel web en hotel Guardado.")
                self.__hotel_web = pickle.load(f)
                # imprimir_hotel_web(self.__hotel_web)
                self.__habitaciones_web = self.__hotel_web.habitacion
        else:
            self.__last_fecha_ingreso = fecha_ingreso
            self.__last_fecha_egreso = fecha_egreso
            self.__last_adultos = adultos
            self.__last_niños = niños
            fecha_ingreso_iso = datetime.strptime(fecha_ingreso, "%d-%m-%Y").strftime("%Y-%m-%d")
            fecha_egreso_iso = datetime.strptime(fecha_egreso, "%d-%m-%Y").strftime("%Y-%m-%d")
            self.__hotel_web = await crawl_alvear(fecha_ingreso_iso, fecha_egreso_iso, adultos, niños)  
            with open("hotel_guardado.pkl", "wb") as f:
                pickle.dump(self.__hotel_web, f)
                imprimir_hotel_web(self.__hotel_web)
                self.__habitaciones_web = self.__hotel_web.habitacion
  
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
      
