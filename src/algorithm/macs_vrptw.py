"""Controlador principal MACS-VRPTW (Figure 2 del artículo)."""

import time
from typing import Any

from loguru import logger

from src.algorithm.acs_time import ACS_TIME
from src.algorithm.acs_vei import ACS_VEI
from src.algorithm.local_search.base import LocalSearchStrategy
from src.heuristics.nearest_neighbor import nearest_neighbor_solution
from src.models.instance import Instance
from src.models.solution import Solution


class MACS_VRPTW:
    """Controlador MACS-VRPTW que coordina dos colonias ACS.

    Implementa el algoritmo principal de Gambardella et al. (1999),
    alternando ciclos de ACS-VEI (minimización de vehículos) y
    ACS-TIME (minimización de distancia).
    """

    def __init__(
        self,
        instance: Instance,
        num_ants: int = 10,
        beta: float = 1.0,
        q0: float = 0.9,
        rho: float = 0.1,
        max_iterations: int = 200,
        max_no_improvement: int = 50,
        local_search: LocalSearchStrategy | None = None,
        on_improvement: Any = None,
        on_iteration: Any = None,
    ) -> None:
        """Inicializa el controlador MACS-VRPTW."""
        self._instance = instance
        self._num_ants = num_ants
        self._beta = beta
        self._q0 = q0
        self._rho = rho
        self._max_iterations = max_iterations
        self._max_no_improvement = max_no_improvement
        self._local_search = local_search
        self._on_improvement = on_improvement
        self._on_iteration = on_iteration
        self._history: list[dict[str, Any]] = []

    @property
    def history(self) -> list[dict[str, Any]]:
        """Historial de mejoras durante la ejecución."""
        return self._history

    def solve(self) -> Solution:
        """Ejecuta el algoritmo MACS-VRPTW completo.

        Returns:
            Mejor solución encontrada (psi_gb).
        """
        start_time = time.time()
        self._history = []

        # Paso 1: Solución inicial con nearest-neighbor (vehículos ilimitados)
        psi_gb = nearest_neighbor_solution(self._instance)
        if not psi_gb.is_feasible(self._instance):
            logger.warning("Solución NN inicial no es factible")

        # Calcular tau_0 = 1 / (n * J_nn)
        nn_cost = psi_gb.total_distance(self._instance)
        n = self._instance.num_customers
        tau_0 = 1.0 / (n * nn_cost) if nn_cost > 0 else 1e-6

        v = psi_gb.num_vehicles()
        logger.info(
            f"Solución inicial: {v} vehículos, distancia={nn_cost:.2f}, tau_0={tau_0:.8f}"
        )

        self._record_improvement(0, psi_gb, start_time, "Solución NN inicial")

        # Loop principal
        iteration = 0
        no_improvement_count = 0

        while iteration < self._max_iterations and no_improvement_count < self._max_no_improvement:
            v = psi_gb.num_vehicles()

            # Crear colonias
            acs_vei = ACS_VEI(
                instance=self._instance,
                num_ants=self._num_ants,
                beta=self._beta,
                q0=self._q0,
                rho=self._rho,
                tau_0=tau_0,
                num_vehicles=max(1, v - 1),  # v - 1 vehículos
            )
            acs_time = ACS_TIME(
                instance=self._instance,
                num_ants=self._num_ants,
                beta=self._beta,
                q0=self._q0,
                rho=self._rho,
                tau_0=tau_0,
                num_vehicles=v,
                local_search=self._local_search,
            )

            vehicle_reduced = False

            # Ciclos internos hasta reducir vehículos o agotar iteraciones
            inner_iterations = min(
                self._max_iterations - iteration, self._max_no_improvement
            )

            for inner in range(inner_iterations):
                iteration += 1
                improved = False

                # Ejecutar ACS-VEI
                self._notify_iteration(iteration, "ACS-VEI", start_time, psi_gb)
                vei_result = acs_vei.run_cycle(psi_gb)
                if vei_result is not None:
                    new_v = vei_result.num_vehicles()
                    if new_v < v:
                        psi_gb = vei_result
                        self._record_improvement(
                            iteration, psi_gb, start_time,
                            f"ACS-VEI: reducción a {new_v} vehículos"
                        )
                        logger.info(
                            f"Iteración {iteration}: ACS-VEI redujo a {new_v} vehículos, "
                            f"distancia={psi_gb.total_distance(self._instance):.2f}"
                        )
                        vehicle_reduced = True
                        no_improvement_count = 0
                        break

                # Ejecutar ACS-TIME
                self._notify_iteration(iteration, "ACS-TIME", start_time, psi_gb)
                time_result = acs_time.run_cycle(psi_gb)
                if time_result is not None:
                    new_dist = time_result.total_distance(self._instance)
                    old_dist = psi_gb.total_distance(self._instance)
                    if new_dist < old_dist:
                        psi_gb = time_result
                        improved = True
                        no_improvement_count = 0
                        self._record_improvement(
                            iteration, psi_gb, start_time,
                            f"ACS-TIME: distancia mejorada a {new_dist:.2f}"
                        )
                        logger.info(
                            f"Iteración {iteration}: ACS-TIME mejoró distancia "
                            f"{old_dist:.2f} -> {new_dist:.2f}"
                        )

                if not improved:
                    no_improvement_count += 1

                if iteration % 25 == 0:
                    elapsed = time.time() - start_time
                    logger.info(
                        f"Iteración {iteration}/{self._max_iterations}: "
                        f"{psi_gb.num_vehicles()} veh, "
                        f"dist={psi_gb.total_distance(self._instance):.2f}, "
                        f"sin_mejora={no_improvement_count}, "
                        f"tiempo={elapsed:.1f}s"
                    )

            if not vehicle_reduced:
                break  # No se pudo reducir vehículos, terminar

        elapsed = time.time() - start_time
        final_dist = psi_gb.total_distance(self._instance)
        final_v = psi_gb.num_vehicles()
        logger.info(
            f"MACS-VRPTW finalizado: {final_v} vehículos, distancia={final_dist:.2f}, "
            f"iteraciones={iteration}, tiempo={elapsed:.1f}s"
        )

        return psi_gb

    def _record_improvement(
        self, iteration: int, solution: Solution, start_time: float, event: str
    ) -> None:
        """Registra una mejora en el historial."""
        entry = {
            "iteration": iteration,
            "num_vehicles": solution.num_vehicles(),
            "total_distance": round(
                solution.total_distance(self._instance), 2
            ),
            "elapsed_time": round(time.time() - start_time, 2),
            "event": event,
        }
        self._history.append(entry)
        if self._on_improvement is not None:
            self._on_improvement(solution, entry)

    def _notify_iteration(
        self, iteration: int, phase: str, start_time: float, solution: Solution
    ) -> None:
        """Notifica el progreso de cada iteración."""
        if self._on_iteration is not None:
            info = {
                "iteration": iteration,
                "max_iterations": self._max_iterations,
                "phase": phase,
                "elapsed_time": round(time.time() - start_time, 2),
                "num_vehicles": solution.num_vehicles(),
                "total_distance": round(
                    solution.total_distance(self._instance), 2
                ),
            }
            self._on_iteration(info)
