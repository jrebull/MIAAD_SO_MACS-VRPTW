"""Clase abstracta base para colonias ACS (SOLID: DIP + OCP)."""

from abc import ABC, abstractmethod

from src.models.instance import Instance
from src.models.solution import Solution


class ColonyBase(ABC):
    """Interfaz base para colonias de hormigas.

    Permite al controlador MACS-VRPTW trabajar con cualquier
    tipo de colonia a través de esta abstracción (Dependency Inversion).
    """

    @abstractmethod
    def run_cycle(self, psi_gb: Solution) -> Solution | None:
        """Ejecuta un ciclo completo de la colonia.

        Args:
            psi_gb: Mejor solución global actual.

        Returns:
            Nueva mejor solución si se encontró mejora, None en caso contrario.
        """
        ...

    @abstractmethod
    def reinitialize(self, num_vehicles: int, psi_gb: Solution) -> None:
        """Reinicializa la colonia con un nuevo número de vehículos."""
        ...
