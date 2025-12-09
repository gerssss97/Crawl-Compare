from pydantic import BaseModel, field_validator, Field
from typing import ClassVar, Optional
from datetime import date

class Periodo(BaseModel):
    nombresito: Optional[str] = ""
    id: int = Field(init=False)  # nuevo id autoincremental, no se permite en init
    fecha_inicio: date
    fecha_fin: date
    # fila: int
    
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
    def crear(cls, fecha_inicio: date, fecha_fin: date, nombre: Optional[str]) -> 'Periodo':
        return cls(
            nombresito = nombre,
            fecha_inicio = fecha_inicio,
            fecha_fin = fecha_fin
        )
