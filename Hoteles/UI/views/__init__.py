"""Views layer - Agrupaciones lógicas de componentes."""

from .vista_resultados import VistaResultados
from .config_modal import ConfigModal
from .historial_modal import HistorialModal
from .resultados_modal import ResultadosModal

__all__ = [
    'VistaResultados',
    'ConfigModal',
    'HistorialModal',
    'ResultadosModal',
]
