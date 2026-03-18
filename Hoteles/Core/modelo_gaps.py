"""Modelos para representar gaps (períodos sin cobertura) en el Excel.

Este módulo define las estructuras de datos para:
- Gap: Un rango de fechas sin precio definido en el Excel
- GapAnalysis: Análisis completo de cobertura para un rango solicitado
"""

from dataclasses import dataclass
from datetime import date
from typing import List


@dataclass
class Gap:
    """Representa un período sin cobertura de precio en Excel."""
    fecha_inicio: date
    fecha_fin: date

    def get_dias(self) -> int:
        return (self.fecha_fin - self.fecha_inicio).days + 1

    def formato_rango(self) -> str:
        return f"{self.fecha_inicio:%d/%m/%Y} - {self.fecha_fin:%d/%m/%Y}"

    def contiene_fecha(self, fecha: date) -> bool:
        return self.fecha_inicio <= fecha <= self.fecha_fin


class GapAnalysis:
    """Resultado de análisis de cobertura para un rango de fechas."""

    def __init__(
        self,
        fecha_entrada: date,
        fecha_salida: date,
        periodos_aplicables: List,
        gaps: List[Gap]
    ):
        self.fecha_entrada = fecha_entrada
        self.fecha_salida = fecha_salida
        self.periodos_aplicables = periodos_aplicables
        self.gaps = gaps
        self.tiene_gaps = len(gaps) > 0
        self.cobertura_total = len(gaps) == 0

    def get_gap_description(self) -> str:
        if not self.gaps:
            return "Cobertura completa"

        descripciones = []
        for gap in self.gaps:
            descripciones.append(f"• {gap.formato_rango()} ({gap.get_dias()} días)")

        return "Sin cobertura Excel en:\n" + "\n".join(descripciones)

    def __repr__(self) -> str:
        return (
            f"GapAnalysis("
            f"periodos={len(self.periodos_aplicables)}, "
            f"gaps={len(self.gaps)}, "
            f"tiene_gaps={self.tiene_gaps}"
            f")"
        )
