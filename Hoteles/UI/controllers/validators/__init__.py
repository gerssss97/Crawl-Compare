"""Subpaquete de validators desacoplados.

Cada validator implementa el protocolo ``Validator`` y devuelve un
``ValidationResult`` con la lista de errores encontrados. No abren UI:
la presentación queda a cargo del orquestador que los invoca.
"""

from .base import ValidationError, ValidationResult, Validator
from .fechas_validator import FechasValidator
from .campos_validator import CamposValidator
from .excel_validator import ExcelCargadoValidator

__all__ = [
    "ValidationError",
    "ValidationResult",
    "Validator",
    "FechasValidator",
    "CamposValidator",
    "ExcelCargadoValidator",
]
