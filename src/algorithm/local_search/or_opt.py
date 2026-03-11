"""Búsqueda local Or-opt: reubicación de 1, 2 o 3 clientes consecutivos."""

from src.algorithm.local_search.base import LocalSearchStrategy
from src.models.instance import Instance
from src.models.solution import Route, Solution


class OrOpt(LocalSearchStrategy):
    """Or-opt: reubica segmentos de 1, 2 o 3 clientes consecutivos.

    Prueba mover segmentos dentro de la misma ruta o entre rutas
    diferentes, aceptando solo mejoras que mantengan factibilidad.
    """

    def apply(self, solution: Solution, instance: Instance) -> Solution:
        """Aplica Or-opt iterativamente hasta que no haya mejora."""
        improved = True
        best = solution.copy()

        while improved:
            improved = False

            for seg_len in [3, 2, 1]:
                result = self._try_or_opt(best, seg_len, instance)
                if result is not None:
                    best = result
                    improved = True
                    break

        return best

    def _try_or_opt(
        self,
        solution: Solution,
        seg_len: int,
        instance: Instance,
    ) -> Solution | None:
        """Intenta reubicar un segmento de longitud seg_len."""
        active = [i for i, r in enumerate(solution.routes) if r.customer_ids]

        best_improvement = 0.0
        best_move = None

        for src_idx in active:
            src_ids = solution.routes[src_idx].customer_ids
            if len(src_ids) < seg_len:
                continue

            for pos in range(len(src_ids) - seg_len + 1):
                segment = src_ids[pos: pos + seg_len]
                remaining = src_ids[:pos] + src_ids[pos + seg_len:]

                src_dist_old = solution.routes[src_idx].total_distance(instance)

                for dst_idx in active:
                    dst_ids = solution.routes[dst_idx].customer_ids

                    if dst_idx == src_idx:
                        # Reubicar dentro de la misma ruta
                        dst_base = remaining
                    else:
                        dst_base = dst_ids

                    for ins_pos in range(len(dst_base) + 1):
                        if dst_idx == src_idx and ins_pos == pos:
                            continue  # Sin cambio

                        new_dst = dst_base[:ins_pos] + segment + dst_base[ins_pos:]

                        if dst_idx == src_idx:
                            new_route = Route(customer_ids=new_dst)
                            if not new_route.is_feasible(instance):
                                continue
                            improvement = src_dist_old - new_route.total_distance(instance)

                            if improvement > best_improvement:
                                best_improvement = improvement
                                best_move = ("intra", src_idx, new_dst)
                        else:
                            new_src_route = Route(customer_ids=remaining)
                            new_dst_route = Route(customer_ids=new_dst)

                            if not new_src_route.is_feasible(instance):
                                continue
                            if not new_dst_route.is_feasible(instance):
                                continue

                            dst_dist_old = solution.routes[dst_idx].total_distance(instance)
                            improvement = (
                                src_dist_old + dst_dist_old
                                - new_src_route.total_distance(instance)
                                - new_dst_route.total_distance(instance)
                            )

                            if improvement > best_improvement:
                                best_improvement = improvement
                                best_move = ("inter", src_idx, remaining, dst_idx, new_dst)

        if best_move is None or best_improvement <= 1e-10:
            return None

        new_solution = solution.copy()
        if best_move[0] == "intra":
            _, r_idx, new_ids = best_move
            new_solution.routes[r_idx] = Route(customer_ids=new_ids)
        else:
            _, src_idx, src_ids, dst_idx, dst_ids = best_move
            new_solution.routes[src_idx] = Route(customer_ids=src_ids)
            new_solution.routes[dst_idx] = Route(customer_ids=dst_ids)

        return new_solution
