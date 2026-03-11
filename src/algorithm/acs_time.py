"""Colonia ACS-TIME: minimización de distancia total (Figure 3 del artículo)."""

from loguru import logger

from src.algorithm.ant import new_active_ant
from src.algorithm.colony_base import ColonyBase
from src.algorithm.local_search.base import LocalSearchStrategy
from src.algorithm.pheromone import PheromoneMatrix
from src.models.instance import Instance
from src.models.solution import Solution


class ACS_TIME(ColonyBase):
    """Colonia ACS-TIME para minimizar la distancia total.

    Opera con un número fijo de vehículos v e intenta encontrar
    soluciones factibles con menor distancia. Usa búsqueda local
    y pasa IN=0 (sin penalización de inserción).
    """

    def __init__(
        self,
        instance: Instance,
        num_ants: int,
        beta: float,
        q0: float,
        rho: float,
        tau_0: float,
        num_vehicles: int,
        local_search: LocalSearchStrategy | None = None,
    ) -> None:
        """Inicializa ACS-TIME.

        Args:
            instance: Instancia VRPTW.
            num_ants: Número de hormigas.
            beta: Peso de la información heurística.
            q0: Probabilidad de explotación.
            rho: Tasa de evaporación.
            tau_0: Valor inicial de feromonas.
            num_vehicles: Número de vehículos permitidos.
            local_search: Estrategia de búsqueda local.
        """
        self._instance = instance
        self._num_ants = num_ants
        self._beta = beta
        self._q0 = q0
        self._rho = rho
        self._tau_0 = tau_0
        self._num_vehicles = num_vehicles
        self._local_search = local_search
        n = instance.num_customers + 1
        self._pheromone = PheromoneMatrix(n, tau_0)

    def run_cycle(self, psi_gb: Solution) -> Solution | None:
        """Ejecuta un ciclo de ACS-TIME (Figure 3).

        Cada hormiga construye una solución con búsqueda local y IN=0.
        Si alguna mejora la mejor global, se retorna.
        Finalmente, actualización global con psi_gb.
        """
        best_improvement: Solution | None = None
        best_dist = psi_gb.total_distance(self._instance)

        ls_fn = self._local_search.apply if self._local_search else None

        for k in range(self._num_ants):
            psi_k = new_active_ant(
                ant_id=k,
                instance=self._instance,
                pheromone=self._pheromone,
                beta=self._beta,
                q0=self._q0,
                rho=self._rho,
                num_vehicles=self._num_vehicles,
                in_vector=None,  # ACS-TIME no usa IN
                apply_local_search=True,
                local_search_fn=ls_fn,
            )

            if psi_k.is_feasible(self._instance):
                dist_k = psi_k.total_distance(self._instance)
                if dist_k < best_dist:
                    best_dist = dist_k
                    best_improvement = psi_k.copy()
                    logger.debug(
                        f"ACS-TIME hormiga {k}: nueva mejor distancia={dist_k:.2f}"
                    )

        # Actualización global con psi_gb (Eq. 2)
        self._pheromone.global_update(psi_gb, self._rho, self._instance)

        return best_improvement

    def reinitialize(self, num_vehicles: int, psi_gb: Solution) -> None:
        """Reinicializa ACS-TIME con nuevo número de vehículos."""
        self._num_vehicles = num_vehicles
        self._pheromone.reinitialize(self._tau_0)
        logger.debug(f"ACS-TIME reinicializada: {num_vehicles} vehículos")
