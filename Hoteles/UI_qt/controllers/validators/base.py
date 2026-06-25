"""Tipos base del esquema de validación."""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ValidationError:
    campo: str          # ej: "fecha_entrada", "excel", "adultos"
    mensaje: str
    severity: str = "error"  # "error" | "warning"


@dataclass
class ValidationResult:
    errors: list[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """True si no hay errores de severidad 'error'."""
        return not any(e.severity == "error" for e in self.errors)

    def merge(self, other: "ValidationResult") -> None:
        self.errors.extend(other.errors)

    def mensajes_concatenados(self) -> str:
        """Bullet list para mostrar todos los errores juntos."""
        return "\n".join(f"• {e.mensaje}" for e in self.errors)


class Validator(Protocol):
    def validate(self, state) -> ValidationResult: ...
