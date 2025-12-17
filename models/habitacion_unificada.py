from pydantic import BaseModel
from typing import List, Optional, Dict
from .hotelExcel import HabitacionExcel


class HabitacionUnificada(BaseModel):
    """Habitación con múltiples variantes de precio según periodo.

    Esta clase agrupa habitaciones con el mismo nombre pero diferentes precios
    y periodos, permitiendo mostrar una sola entrada en la UI mientras se mantiene
    la información de todas las variantes.

    Ejemplo:
        nombre = "dbl superior"
        variantes = [
            HabitacionExcel(nombre="dbl superior", precio=150.0, periodo_ids={1}),
            HabitacionExcel(nombre="dbl superior", precio=180.0, periodo_ids={2, 3}),
            HabitacionExcel(nombre="dbl superior", precio=200.0, periodo_ids={4})
        ]
    """

    nombre: str  # Nombre normalizado de la habitación
    variantes: List[HabitacionExcel]  # Todas las variantes de precio/periodo

    def precio_para_periodo(self, periodo_id: int) -> Optional[float | str]:
        """Retorna el precio de la variante que contiene el periodo_id especificado.

        Args:
            periodo_id: ID del periodo para el cual se busca el precio

        Returns:
            - float: Precio numérico de la habitación en ese periodo
            - str: Leyenda especial ("closing agreement", etc.)
            - None: Si no hay variante para ese periodo
        """
        for variante in self.variantes:
            if periodo_id in variante.periodo_ids:
                # Si tiene precio numérico, retornarlo
                if variante.precio is not None:
                    return variante.precio
                # Si tiene precio_string (leyenda), retornarlo
                if variante.precio_string is not None:
                    return variante.precio_string
                # Si no tiene ni precio ni precio_string
                return None
        return None

    def precios_para_periodos(self, periodo_ids: set[int]) -> Dict[int, float | str]:
        """Retorna un diccionario {periodo_id: precio} para un conjunto de periodos.

        Útil para mostrar múltiples precios cuando el rango de fechas abarca
        varios periodos.

        Args:
            periodo_ids: Set de IDs de periodos

        Returns:
            Diccionario con periodo_id como clave y precio como valor
        """
        resultado = {}
        for pid in periodo_ids:
            precio = self.precio_para_periodo(pid)
            if precio is not None:
                resultado[pid] = precio
        return resultado

    def todos_los_periodos(self) -> set[int]:
        """Retorna todos los periodo_ids de todas las variantes.

        Returns:
            Set con la unión de todos los periodo_ids de todas las variantes
        """
        todos = set()
        for variante in self.variantes:
            todos.update(variante.periodo_ids)
        return todos

    def variante_para_periodo(self, periodo_id: int) -> Optional[HabitacionExcel]:
        """Retorna la variante completa (HabitacionExcel) para un periodo específico.

        Args:
            periodo_id: ID del periodo

        Returns:
            HabitacionExcel completo que aplica para ese periodo, o None
        """
        for variante in self.variantes:
            if periodo_id in variante.periodo_ids:
                return variante
        return None
