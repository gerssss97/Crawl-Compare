from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class ComboPrecio(BaseModel):
    titulo: str
    descripcion: str
    precio: float

class HabitacionWeb(BaseModel):
    nombre: str
    detalles: Optional[str]
    combos: List[ComboPrecio]
    impuestos: Optional[float] = None

    def precio_total(self, combo_idx: int = 0) -> float:
        """Retorna el precio total (base + impuestos) para un combo."""
        base = self.combos[combo_idx].precio if self.combos else 0.0
        return base + (self.impuestos or 0.0)

class HotelWeb(BaseModel):
    habitacion: List[HabitacionWeb]
    detalles: str
    url_visitada: Optional[str] = None

class ParametrosBusqueda(BaseModel):
    fecha_entrada: date
    fecha_salida: date
    adultos: int
    ninos: int

def imprimir_hotel_web(hotel: HotelWeb):
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

def print_habitacion_web(habitacion: HotelWeb):
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

def generar_blanco(texto):
    longitud = len(texto)
    return f"{'':<{longitud}}"

def imprimir_habitacion_web(habitacion):
    # Usamos una lista para construir las líneas y luego las unimos
    lineas = []
    lineas.append(f"🏠 Habitación: {habitacion.nombre}")

    if habitacion.detalles:
        lineas.append(f"📋 Detalles:")
        espacio_blanco = generar_blanco("📋 Detalles:")
        for linea in habitacion.detalles.splitlines():
            lineas.append(f"{espacio_blanco} {linea}")

    if habitacion.combos:
        lineas.append("  💼 Combos:")
        espacio_blanco = generar_blanco("  💼 Combos:")
        for idx, combo in enumerate(habitacion.combos):
            lineas.append(f"{espacio_blanco} 🟦 {combo.titulo.upper()} 🟦")
            lineas.append(f"{espacio_blanco} 📃 {combo.descripcion}")
            lineas.append(f"{espacio_blanco} 💵 ${combo.precio:.2f}")
            if habitacion.impuestos is not None:
                lineas.append(f"{espacio_blanco} 🏛️ Impuestos: ${habitacion.impuestos:.2f}")
                total = habitacion.precio_total(idx)
                lineas.append(f"{espacio_blanco} 💰 TOTAL: ${total:.2f}")
    else:
        lineas.append("  ❌ Sin promociones registradas.")

    return "\n".join(lineas)

