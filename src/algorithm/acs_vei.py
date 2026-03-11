"""Colonia ACS-VEI: minimización del número de vehículos (Figure 4 del artículo)."""

import numpy as np
from loguru import logger

from src.algorithm.ant import new_active_ant
from src.algorithm.colony_base import ColonyBase
from src.algorithm.pheromone import PheromoneMatrix
from src.heuristics.nearest_neighbor import nearest_neighbor_solution
from src.models.instance import Instance
from src.models.solution import Solution


class ACS_VEI(ColonyBase):
    """Colonia ACS-VEI para minimizar el número de vehículos.

    Opera con s = v-1 vehículos (uno menos que la mejor global)
    e intenta encontrar soluciones factibles. Mantiene un vector IN
    que penaliza clientes frecuentemente no visitados.
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
    ) -> None:
        """Inicializa ACS-VEI.

        Args:
            instance: Instancia VRPTW.
            num_ants: Número de hormigas.
            beta: Peso de la información heurística.
            q0: Probabilidad de explotación.
            rho: Tasa de evaporación.
            tau_0: Valor inicial de feromonas.
            num_vehicles: Número de vehículos objetivo (v-1).
        """
        self._instance = instance
        self._num_ants = num_ants
        self._beta = beta
        self._q0 = q0
        self._rho = rho
        self._tau_0 = tau_0
        self._num_vehicles = num_vehicles
        n = instance.num_customers + 1
        self._pheromone = PheromoneMatrix(n, tau_0)

        # Vector IN: cuenta cuántas veces un cliente no fue visitado
        self._in_vector = np.zeros(n, dtype=np.float64)

        # Mejor solución local de ACS-VEI (puede ser infactible)
        self._psi_vei: Solution = nearest_neighbor_solution(instance, num_vehicles)

    def run_cycle(self, psi_gb: Solution) -> Solution | None:
        """Ejecuta un ciclo de ACS-VEI (Figure 4).

        Cada hormiga construye sin búsqueda local; se actualiza IN
        por clientes no visitados. Si alguna hormiga visita más clientes
        que psi_vei, se actualiza psi_vei y se resetea IN.
        Doble actualización global: con psi_vei y con psi_gb.
        """
        best_served = self._psi_vei.num_served_customers()
        found_feasible: Solution | None = None

        for k in range(self._num_ants):
            psi_k = new_active_ant(
                ant_id=k,
                instance=self._instance,
                pheromone=self._pheromone,
                beta=self._beta,
                q0=self._q0,
                rho=self._rho,
                num_vehicles=self._num_vehicles,
                in_vector=self._in_vector,
                apply_local_search=False,
                local_search_fn=None,
            )

            served_k = psi_k.num_served_customers()

            # Actualizar IN: incrementar para clientes no visitados
            served_set = psi_k.get_all_served_customers()
            for c in self._instance.customers:
                if c.id not in served_set:
                    self._in_vector[c.id] += 1

            # Verificar si esta hormiga visitó más clientes
            if served_k > best_served:
                best_served = served_k
                self._psi_vei = psi_k.copy()
                self._in_vector[:] = 0  # Resetear IN
                logger.debug(
                    f"ACS-VEI hormiga {k}: mejor cobertura={served_k}/{self._instance.num_customers}"
                )

                if psi_k.is_feasible(self._instance):
                    found_feasible = psi_k.copy()
                    logger.info(
                        f"ACS-VEI: solución factible con {psi_k.num_vehicles()} vehículos, "
                        f"distancia={psi_k.total_distance(self._instance):.2f}"
                    )

        # Doble actualización global (Eq. 2)
        self._pheromone.global_update(self._psi_vei, self._rho, self._instance)
        self._pheromone.global_update(psi_gb, self._rho, self._instance)

        return found_feasible

    def reinitialize(self, num_vehicles: int, psi_gb: Solution) -> None:
        """Reinicializa ACS-VEI con nuevo número de vehículos."""
        self._num_vehicles = num_vehicles
        self._pheromone.reinitialize(self._tau_0)
        self._in_vector[:] = 0
        self._psi_vei = nearest_neighbor_solution(self._instance, num_vehicles)
        logger.debug(f"ACS-VEI reinicializada: {num_vehicles} vehículos")
