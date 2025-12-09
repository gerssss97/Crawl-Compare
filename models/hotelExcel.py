from pydantic import BaseModel, field_validator, Field, model_validator
from typing import List, Optional, Union
from .periodo import Periodo

def normalizar_precio_str(s: str) -> Optional[float]:
    try:
        cleaned = s.replace("$", "").replace("€", "").replace(",", "").strip()
        valor = float(cleaned)
        return round(valor, 2)
    except Exception:
        return None

LEYENDAS_AGREEMENT = [
    "closing agreement",
    "bar 20% com"
]

class PeriodoGroup(BaseModel):
    nombre: str
    periodos: List[Periodo]

class HabitacionExcel(BaseModel):
    nombre: str
    precio: Optional[Union[float, str]] = None
    precio_string: Optional[str] = None
    row_idx: int
    periodo_ids: set[int] = Field(default_factory = set)  
    
   
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

class Extra(BaseModel):
    nombre: str
    precio: Optional[float] = None

class HotelExcel(BaseModel):
    nombre: str
    tipos: List[TipoHabitacionExcel] = Field(default_factory=list)
    habitaciones_directas: List[HabitacionExcel] = Field(default_factory=list)
    periodos_group: List [PeriodoGroup] = Field(default_factory=list)
    extras: list[Extra] = Field(default_factory=list)

    def periodo_por_id(self, pid: int) -> Optional[Periodo]:
        for p in self.periodos_group:
            for p in p.periodos:
                if p.id == pid:
                    return p
        return None


class DatosExcel(BaseModel):
    hoteles: List[HotelExcel]