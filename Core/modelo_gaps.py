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
    """Representa un período sin cobertura de precio en Excel.

    Atributos:
        fecha_inicio: Primer día sin cobertura
        fecha_fin: Último día sin cobertura

    Ejemplo:
        Gap(date(2025, 10, 1), date(2026, 4, 30))
        representa el rango 01/10/2025 - 30/04/2026 sin precio Excel
    """
    fecha_inicio: date
    fecha_fin: date

    def get_dias(self) -> int:
        """Calcula cantidad de días en el gap.

        Returns:
            Número de días inclusive (fecha_fin - fecha_inicio + 1)
        """
        return (self.fecha_fin - self.fecha_inicio).days + 1

    def formato_rango(self) -> str:
        """Retorna representación legible del rango de fechas.

        Returns:
            String en formato "DD/MM/AAAA - DD/MM/AAAA"

        Ejemplo:
            "01/10/2025 - 30/04/2026"
        """
        return f"{self.fecha_inicio:%d/%m/%Y} - {self.fecha_fin:%d/%m/%Y}"

    def contiene_fecha(self, fecha: date) -> bool:
        """Verifica si una fecha cae dentro del gap.

        Args:
            fecha: Fecha a verificar

        Returns:
            True si la fecha está dentro del gap, False si no
        """
        return self.fecha_inicio <= fecha <= self.fecha_fin


class GapAnalysis:
    """Resultado de análisis de cobertura para un rango de fechas.

    Analiza un rango solicitado (fecha_entrada → fecha_salida) y determina:
    - Qué periodos del Excel aplican (tienen overlap)
    - Qué rangos NO tienen cobertura (gaps)

    Atributos:
        fecha_entrada: Fecha de check-in solicitada
        fecha_salida: Fecha de check-out solicitada
        periodos_aplicables: Periodos del Excel que tienen overlap con el rango
        gaps: Rangos sin cobertura de precio
        tiene_gaps: True si hay al menos un gap
        cobertura_total: True si NO hay gaps (cobertura 100%)

    Ejemplo:
        Rango: 11/06/2025 → 11/06/2026
        Excel: 01/05-30/09/2025 y 01/05-30/09/2026

        GapAnalysis(
            periodos_aplicables=[periodo1, periodo2],
            gaps=[Gap(01/10/2025, 30/04/2026)],
            tiene_gaps=True
        )
    """

    def __init__(
        self,
        fecha_entrada: date,
        fecha_salida: date,
        periodos_aplicables: List,  # List[Periodo]
        gaps: List[Gap]
    ):
        """Inicializa el análisis de cobertura.

        Args:
            fecha_entrada: Fecha de check-in solicitada
            fecha_salida: Fecha de check-out solicitada
            periodos_aplicables: Periodos con overlap
            gaps: Rangos sin cobertura
        """
        self.fecha_entrada = fecha_entrada
        self.fecha_salida = fecha_salida
        self.periodos_aplicables = periodos_aplicables
        self.gaps = gaps
        self.tiene_gaps = len(gaps) > 0
        self.cobertura_total = len(gaps) == 0

    def get_gap_description(self) -> str:
        """Genera descripción legible de gaps para mostrar en UI.

        Returns:
            String multilinea con lista de gaps o "Cobertura completa"

        Ejemplo:
            "Sin cobertura Excel en:\n• 01/10/2025 - 30/04/2026 (213 días)"
        """
        if not self.gaps:
            return "Cobertura completa"

        descripciones = []
        for gap in self.gaps:
            descripciones.append(f"• {gap.formato_rango()} ({gap.get_dias()} días)")

        return "Sin cobertura Excel en:\n" + "\n".join(descripciones)

    def __repr__(self) -> str:
        """Representación para debugging."""
        return (
            f"GapAnalysis("
            f"periodos={len(self.periodos_aplicables)}, "
            f"gaps={len(self.gaps)}, "
            f"tiene_gaps={self.tiene_gaps}"
            f")"
        )
