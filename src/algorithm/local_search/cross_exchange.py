"""Búsqueda local CROSS exchange (Section 5.4.3 del artículo)."""

from src.algorithm.local_search.base import LocalSearchStrategy
from src.models.instance import Instance
from src.models.solution import Route, Solution


MAX_SEGMENT_LENGTH = 4  # Longitud máxima de segmentos a intercambiar


class CrossExchange(LocalSearchStrategy):
    """Intercambio de sub-cadenas entre rutas (CROSS exchange).

    Intercambia segmentos de clientes entre dos rutas diferentes,
    aceptando solo movimientos que mejoren la distancia total
    manteniendo la factibilidad.
    """

    def apply(self, solution: Solution, instance: Instance) -> Solution:
        """Aplica CROSS exchange iterativamente hasta que no haya mejora."""
        improved = True
        best = solution.copy()

        while improved:
            improved = False
            active_routes = [
                i for i, r in enumerate(best.routes) if r.customer_ids
            ]

            for idx_a in range(len(active_routes)):
                for idx_b in range(idx_a + 1, len(active_routes)):
                    ra = active_routes[idx_a]
                    rb = active_routes[idx_b]

                    result = self._try_cross_exchange(best, ra, rb, instance)
                    if result is not None:
                        best = result
                        improved = True
                        break
                if improved:
                    break

        return best

    def _try_cross_exchange(
        self,
        solution: Solution,
        ra_idx: int,
        rb_idx: int,
        instance: Instance,
    ) -> Solution | None:
        """Intenta intercambiar segmentos entre dos rutas.

        Usa un enfoque eficiente: solo prueba segmentos cortos (hasta
        MAX_SEGMENT_LENGTH) y retorna el primer movimiento con mejora.
        """
        route_a = solution.routes[ra_idx]
        route_b = solution.routes[rb_idx]
        ids_a = route_a.customer_ids
        ids_b = route_b.customer_ids

        current_dist = (
            route_a.total_distance(instance) + route_b.total_distance(instance)
        )

        # Probar intercambios de segmentos cortos
        for seg_len_a in range(MAX_SEGMENT_LENGTH + 1):
            for seg_len_b in range(MAX_SEGMENT_LENGTH + 1):
                if seg_len_a == 0 and seg_len_b == 0:
                    continue

                for i1 in range(len(ids_a) - seg_len_a + 1):
                    seg_a = ids_a[i1: i1 + seg_len_a]
                    remaining_a = ids_a[:i1] + ids_a[i1 + seg_len_a:]

                    for j1 in range(len(ids_b) - seg_len_b + 1):
                        seg_b = ids_b[j1: j1 + seg_len_b]

                        new_ids_a = ids_a[:i1] + seg_b + ids_a[i1 + seg_len_a:]
                        new_ids_b = ids_b[:j1] + seg_a + ids_b[j1 + seg_len_b:]

                        if not new_ids_a and not new_ids_b:
                            continue

                        new_route_a = Route(customer_ids=new_ids_a)
                        new_route_b = Route(customer_ids=new_ids_b)

                        # Verificar factibilidad rápida (capacidad primero)
                        if new_ids_a:
                            demand_a = sum(instance.all_nodes[c].demand for c in new_ids_a)
                            if demand_a > instance.capacity:
                                continue
                        if new_ids_b:
                            demand_b = sum(instance.all_nodes[c].demand for c in new_ids_b)
                            if demand_b > instance.capacity:
                                continue

                        if not new_route_a.is_feasible(instance):
                            continue
                        if not new_route_b.is_feasible(instance):
                            continue

                        new_dist = (
                            new_route_a.total_distance(instance)
                            + new_route_b.total_distance(instance)
                        )

                        if current_dist - new_dist > 1e-10:
                            new_solution = solution.copy()
                            new_solution.routes[ra_idx] = new_route_a
                            new_solution.routes[rb_idx] = new_route_b
                            return new_solution

        return None
