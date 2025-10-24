from pydantic import BaseModel, field_validator, Field, model_validator
from typing import List, Optional, ClassVar, Union
from datetime import date


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
        for combo in habitacion.combos:
            lineas.append(f"{espacio_blanco} 🟦 {combo.titulo.upper()} 🟦")
            lineas.append(f"{espacio_blanco} 📃 {combo.descripcion}")
            lineas.append(f"{espacio_blanco} 💵 ${combo.precio:.2f}")
    else:
        lineas.append("  ❌ Sin promociones registradas.")
    
    # Unimos todas las líneas en una única cadena de texto con saltos de línea
    return "\n".join(lineas)

#######################################################


class Periodo(BaseModel):
    id: int = Field(init=False)  # nuevo id autoincremental, no se permite en init
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    
    # Contador de clase para el autoincremento
    _contador: ClassVar[int] = 0 
    
    def __init__(self, **data):
        Periodo._contador += 1
        data['id'] = Periodo._contador  # Siempre asignamos un nuevo ID
        super().__init__(**data)

    @field_validator("fecha_fin")
    @classmethod
    def validar_fechas(cls, v, info):
        if v < info.data["fecha_inicio"]:
            raise ValueError("fecha_fin debe ser igual o posterior a fecha_inicio")
        return v
    @classmethod
    def crear(cls, fecha_inicio: date, fecha_fin: date, nombre: str) -> 'Periodo':
        return cls(
            nombre=nombre,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )


def normalizar_precio_str(s: str) -> Optional[float]:
    try:
        cleaned = s.replace("$", "").replace("€", "").replace(",", "").strip()
        valor = float(cleaned)
        return round(valor, 2)
    except Exception:
        return None

LEYENDAS_AGREEMENT = [
    "closing agreement",
    "a convenir",
    "price on request"
]

class HabitacionExcel(BaseModel):
    nombre: str
    precio: Optional[Union[float, str]] = None
    precio_string: Optional[str] = None
    row_idx: int
    periodo_ids: List[int] = Field(default_factory=list)  # nueva versión con IDs enteros
    
    
   
    @field_validator("nombre", mode="before")
    @classmethod
    def limpiar_nombre(cls, v):
        if v is None:
            raise ValueError("nombre no puede ser None")
        nombre = str(v).strip().lower()
        return nombre

    # 💰 Procesar precio (puede venir numérico o como texto especial)
    @field_validator("precio", mode="before")
    @classmethod
    def procesar_precio(cls, v):
        if v is None:
            return None

        s = str(v).strip().lower()

        # Si coincide con alguna leyenda especial, la devolvemos tal cual
        if s in LEYENDAS_AGREEMENT:
            return s

        # Intentar convertir a número
        valor = normalizar_precio_str(s)
        if valor is None:
            raise ValueError(
                f"Precio inválido: '{v}'. Debe ser un número o una de las leyendas permitidas: {LEYENDAS_AGREEMENT}"
            )
        return valor

    # ⚖️ Validación global (coherencia entre precio y precio_string)
    @model_validator(mode="after")
    def validar_coherencia(cls, values):
        precio = values.precio
        precio_str = values.precio_string

        # Si el precio resultó ser una leyenda textual, moverlo al campo correcto
        if isinstance(precio, str) and precio.lower() in LEYENDAS_AGREEMENT:
            values.precio_string = precio
            values.precio = None

        # No se permiten ambos campos con valor simultáneo
        if values.precio is not None and values.precio_string is not None:
            raise ValueError("No puede haber un precio numérico y un string al mismo tiempo.")

        return values

class TipoHabitacionExcel(BaseModel):
    nombre: str
    habitaciones: List[HabitacionExcel] = Field(default_factory=list)


class HotelExcel(BaseModel):
    nombre: str
    tipos: List[TipoHabitacionExcel] = Field(default_factory=list)
    habitaciones_directas: List[HabitacionExcel] = Field(default_factory=list)
    periodos: List[Periodo] = Field(default_factory=list)

    def periodo_por_id(self, pid: int) -> Optional[Periodo]:
        for p in self.periodos:
            if p.id == pid:
                return p
        return None


class DatosExcel(BaseModel):
    hoteles: List[HotelExcel]