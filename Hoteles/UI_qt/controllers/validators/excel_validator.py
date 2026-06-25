"""Validator defensivo: verifica que haya un Excel cargado.

La UI ya deshabilita el botón "Ejecutar Comparación" cuando no hay Excel.
Este validator existe como red de seguridad ante bugs/eventos perdidos
que pudieran dejar el botón habilitado sin estado válido.
"""

from Core.controller import GestorService
from .base import ValidationError, ValidationResult


class ExcelCargadoValidator:
    def validate(self, state) -> ValidationResult:
        result = ValidationResult()
        if not GestorService.esta_cargado():
            result.errors.append(ValidationError(
                campo="excel",
                mensaje=(
                    "No hay archivo Excel cargado. Seleccioná uno desde "
                    "la barra superior."
                ),
            ))
        return result
