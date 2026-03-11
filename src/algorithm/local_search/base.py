"""Clase abstracta para estrategias de búsqueda local (SOLID: OCP)."""

from abc import ABC, abstractmethod

from src.models.instance import Instance
from src.models.solution import Solution


class LocalSearchStrategy(ABC):
    """Interfaz base para estrategias de búsqueda local.

    Permite extender con nuevas estrategias sin modificar
    el código existente (Open/Closed Principle).
    """

    @abstractmethod
    def apply(self, solution: Solution, instance: Instance) -> Solution:
        """Aplica la búsqueda local a una solución.

        Args:
            solution: Solución factible a mejorar.
            instance: Instancia VRPTW.

        Returns:
            Solución mejorada (o la misma si no hay mejora).
        """
        ...
