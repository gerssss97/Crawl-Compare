from pydantic import BaseModel, field_validator, ValidationInfo, computed_field
from typing import List, Optional
from datetime import date
import string

class ComboPrecio(BaseModel):
    titulo: str
    descripcion: str  
    precio: float     

class Habitacion(BaseModel):
    nombre: str
    detalles: Optional[str]
    combos: List[ComboPrecio]

class Hotel(BaseModel):
    habitacion: List[Habitacion]
    detalles: str


class ParametrosBusqueda(BaseModel):
    fecha_entrada: date
    fecha_salida: date
    adultos: int
    ninos: int

def imprimir_hotel_web(hotel):
    print(f"\n🏨 Hotel: {hotel.detalles}")
    print("=" * (8 + len(hotel.detalles)))

    for i, habitacion in enumerate(hotel.habitacion, start=1):
        print(f"\n🛏️ Habitación {i}: {habitacion.nombre}")
        if habitacion.detalles:
            print(f"   📋 Detalles: {habitacion.detalles}")
        
        if habitacion.combos:
            print("   💼 Combos:")
            for combo in habitacion.combos:
                print(f"     🔹 {combo.titulo}")
                print(f"        📃 {combo.descripcion}")
                print(f"        💵 ${combo.precio:.2f}")
        else:
            print("   ❌ Sin promociones registradas.")   
            
def print_habitacion_web(habitacion):
    print(f"🛏️ Habitación COINCIDENTE: {habitacion.nombre}")
    if habitacion.detalles:
        print(f"   📋 Detalles: {habitacion.detalles}")
    
    if habitacion.combos:
        print("   💼 Combos:")
        for combo in habitacion.combos:
            print(f"     🔹 {combo.titulo}")
            print(f"        📃 {combo.descripcion}")
            print(f"        💵 ${combo.precio:.2f}")
    else:
        print("   ❌ Sin promociones registradas.")   

def imprimir_habitacion_web(habitacion):
    # Usamos una lista para construir las líneas y luego las unimos
    lineas = []
    lineas.append(f"🛏️ Habitación COINCIDENTE: {habitacion.nombre}")

    if habitacion.detalles:
        lineas.append(f"  📋 Detalles: {habitacion.detalles}")
    
    if habitacion.combos:
        lineas.append("  💼 Combos:")
        for combo in habitacion.combos:
            lineas.append(f"    🔹 {combo.titulo}")
            lineas.append(f"      📃 {combo.descripcion}")
            lineas.append(f"      💵 ${combo.precio:.2f}")
    else:
        lineas.append("  ❌ Sin promociones registradas.")
    
    # Unimos todas las líneas en una única cadena de texto con saltos de línea
    return "\n".join(lineas)        

#######################################################


def normalizar_precio_str(s: str) -> Optional[float]:
    try:
        cleaned = s.replace("$", "").replace("€", "").replace(",", "").strip()
        return float(cleaned)
    except Exception:
        return None

class HabitacionExcel(BaseModel):
    nombre: str
    precio: Optional[float] = None
    row_idx: int

    @field_validator("nombre", mode="before")
    @classmethod
    def limpiar_nombre(cls, v):
        if v is None:
            raise ValueError("nombre no puede ser None")
        nombre = str(v).strip().lower()
        return nombre

    @field_validator("precio", mode="before")
    @classmethod
    def normalizar_raw(cls, v):
        if v is None:
            return None
        s = str(v).strip()
        s = normalizar_precio_str(s)
        return s if s != "" else None


class TipoHabitacionExcel(BaseModel):
    nombre: str
    habitaciones: list[HabitacionExcel] = []


class HotelExcel(BaseModel):
    nombre: str
    tipos: list[TipoHabitacionExcel] = []
    habitaciones_directas: list[HabitacionExcel] = []  


class DatosExcel(BaseModel):
    hoteles: list[HotelExcel]