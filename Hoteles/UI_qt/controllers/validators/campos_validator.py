"""Validator de campos completos del formulario."""

from .base import ValidationError, ValidationResult


class CamposValidator:
    CAMPOS = [
        ("Fecha de entrada",   "fecha_entrada_completa"),
        ("Fecha de salida",    "fecha_salida_completa"),
        ("Número de adultos",  "adultos"),
        ("Número de niños",    "ninos"),
        ("Habitación Excel",   "habitacion"),
        ("Precio",             "precio"),
    ]
    VACIOS = ("", None, "(ninguna seleccionada)")

    def validate(self, state) -> ValidationResult:
        result = ValidationResult()
        for nombre_display, attr in self.CAMPOS:
            valor = getattr(state, attr).get()

            if valor in self.VACIOS:
                result.errors.append(ValidationError(
                    campo=attr,
                    mensaje=f"El campo '{nombre_display}' no puede estar vacío.",
                ))
                continue

            if attr == "adultos":
                try:
                    if int(valor) <= 0:
                        result.errors.append(ValidationError(
                            campo=attr,
                            mensaje="Debe haber al menos 1 adulto.",
                        ))
                except (ValueError, TypeError):
                    result.errors.append(ValidationError(
                        campo=attr,
                        mensaje="El número de adultos debe ser un valor numérico válido.",
                    ))
        return result
