"""Gestión de la matriz de feromonas para ACS."""

import numpy as np

from src.models.instance import Instance
from src.models.solution import Solution


class PheromoneMatrix:
    """Matriz de feromonas con operaciones de actualización ACS.

    Implementa las ecuaciones 2 (global) y 3 (local) del artículo
    de Gambardella et al. (1999).
    """

    def __init__(self, n: int, tau_0: float) -> None:
        """Inicializa la matriz de feromonas.

        Args:
            n: Número total de nodos (depósito + clientes).
            tau_0: Valor inicial de feromonas.
        """
        self._n = n
        self._tau_0 = tau_0
        self._matrix = np.full((n, n), tau_0, dtype=np.float64)

    @property
    def tau_0(self) -> float:
        """Valor inicial de feromonas."""
        return self._tau_0

    def get(self, i: int, j: int) -> float:
        """Retorna el nivel de feromona en el arco (i, j)."""
        return float(self._matrix[i, j])

    def local_update(self, i: int, j: int, rho: float) -> None:
        """Actualización local de feromonas (Eq. 3).

        tau_ij = (1 - rho) * tau_ij + rho * tau_0
        """
        self._matrix[i, j] = (1 - rho) * self._matrix[i, j] + rho * self._tau_0
        self._matrix[j, i] = self._matrix[i, j]

    def global_update(self, solution: Solution, rho: float, instance: Instance) -> None:
        """Actualización global de feromonas (Eq. 2).

        Para cada arco (i,j) en la solución:
            tau_ij = (1 - rho) * tau_ij + rho / J(solution)
        """
        cost = solution.total_distance(instance)
        if cost <= 0:
            return

        delta = rho / cost

        for route in solution.routes:
            if not route.customer_ids:
                continue
            edges = self._get_route_edges(route.customer_ids)
            for i, j in edges:
                self._matrix[i, j] = (1 - rho) * self._matrix[i, j] + delta
                self._matrix[j, i] = self._matrix[i, j]

    def reinitialize(self, tau_0: float | None = None) -> None:
        """Reinicializa toda la matriz con tau_0."""
        val = tau_0 if tau_0 is not None else self._tau_0
        self._tau_0 = val
        self._matrix[:] = val

    @staticmethod
    def _get_route_edges(customer_ids: list[int]) -> list[tuple[int, int]]:
        """Extrae los arcos de una ruta (incluyendo depósito)."""
        edges = [(0, customer_ids[0])]
        for k in range(len(customer_ids) - 1):
            edges.append((customer_ids[k], customer_ids[k + 1]))
        edges.append((customer_ids[-1], 0))
        return edges
