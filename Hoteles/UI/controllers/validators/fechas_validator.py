"""Validator de fechas: formato, no-pasado y orden entrada<salida."""

from datetime import datetime
from typing import Optional

from .base import ValidationError, ValidationResult


class FechasValidator:
    def validate(self, state) -> ValidationResult:
        result = ValidationResult()
        fe = state.fecha_entrada_completa.get()
        fs = state.fecha_salida_completa.get()

        fe_dt = self._parsear(fe, "entrada", result)
        fs_dt = self._parsear(fs, "salida", result)

        if fe_dt and fs_dt and fs_dt <= fe_dt:
            result.errors.append(ValidationError(
                campo="fecha_salida",
                mensaje="La fecha de salida debe ser posterior a la de entrada.",
            ))
        return result

    def _parsear(self, fecha_str: str, nombre: str, result: ValidationResult) -> Optional[datetime]:
        # Si está vacía, CamposValidator ya lo reporta — no duplicamos error
        if not fecha_str:
            return None
        try:
            dt = datetime.strptime(fecha_str, "%d-%m-%Y")
        except ValueError:
            result.errors.append(ValidationError(
                campo=f"fecha_{nombre}",
                mensaje=f"La fecha de {nombre} debe tener formato DD-MM-AAAA y ser válida.",
            ))
            return None

        if datetime.now() > dt:
            result.errors.append(ValidationError(
                campo=f"fecha_{nombre}",
                mensaje=f"La fecha de {nombre} debe ser mayor o igual a la actual.",
            ))
            return None
        return dt
