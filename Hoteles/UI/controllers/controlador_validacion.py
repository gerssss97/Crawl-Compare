"""Orquestador de validaciones.

Combina una lista de ``Validator`` y devuelve un ``ValidationResult``.
No abre UI — la presentación de errores queda a cargo de quien invoca
(típicamente ``ControladorComparacion``).
"""

from typing import Optional

from .validators import (
    CamposValidator,
    ExcelCargadoValidator,
    FechasValidator,
    ValidationResult,
    Validator,
)


class ControladorValidacion:
    """Orquesta una lista de validators contra el AppState."""

    def __init__(self, estado_app, validators: Optional[list[Validator]] = None):
        self.estado_app = estado_app
        # Orden importante: Excel primero (si falta, lo demás no tiene sentido),
        # después campos, después fechas (que asume campos completos).
        self._validators: list[Validator] = validators or [
            ExcelCargadoValidator(),
            CamposValidator(),
            FechasValidator(),
        ]

    def validar_todo(self) -> ValidationResult:
        result = ValidationResult()
        for v in self._validators:
            result.merge(v.validate(self.estado_app))
        return result
