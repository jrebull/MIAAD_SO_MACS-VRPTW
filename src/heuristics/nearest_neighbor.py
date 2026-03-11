"""Heurística de vecino más cercano para generar solución inicial del VRPTW."""

from loguru import logger

from src.models.instance import Instance
from src.models.solution import Route, Solution


def nearest_neighbor_solution(
    instance: Instance,
    num_vehicles: int | None = None,
) -> Solution:
    """Construye una solución VRPTW usando la heurística del vecino más cercano.

    Args:
        instance: Instancia VRPTW.
        num_vehicles: Si None, usa vehículos ilimitados (solución inicial MACS).
                      Si N, intenta construir con exactamente N vehículos (puede ser infactible).

    Returns:
        Solución construida (puede ser infactible si num_vehicles es limitado).
    """
    unvisited = {c.id for c in instance.customers}
    routes: list[Route] = []
    max_routes = num_vehicles if num_vehicles else instance.num_customers

    while unvisited and len(routes) < max_routes:
        route_ids: list[int] = []
        current_id = 0
        current_time = 0.0
        current_load = 0

        while True:
            best_id = -1
            best_dist = float("inf")

            for cid in unvisited:
                customer = instance.all_nodes[cid]
                travel = instance.distance(current_id, cid)
                arrival = current_time + travel
                start_service = max(arrival, customer.ready_time)

                # Verificar factibilidad
                if start_service > customer.due_date:
                    continue
                if current_load + customer.demand > instance.capacity:
                    continue

                # Verificar retorno al depósito
                return_time = start_service + customer.service_time + instance.distance(cid, 0)
                if return_time > instance.depot.due_date:
                    continue

                if travel < best_dist:
                    best_dist = travel
                    best_id = cid

            if best_id == -1:
                break

            customer = instance.all_nodes[best_id]
            travel = instance.distance(current_id, best_id)
            arrival = current_time + travel
            current_time = max(arrival, customer.ready_time) + customer.service_time
            current_load += customer.demand
            route_ids.append(best_id)
            unvisited.discard(best_id)
            current_id = best_id

        if route_ids:
            routes.append(Route(customer_ids=route_ids))

    # Si quedan clientes sin servir y num_vehicles forzado, crear ruta extra (infactible)
    if unvisited and num_vehicles:
        remaining = sorted(unvisited)
        # Distribuir en rutas existentes si es posible, o la última
        if routes:
            routes[-1].customer_ids.extend(remaining)
        else:
            routes.append(Route(customer_ids=remaining))

    solution = Solution(routes=routes)
    dist = solution.total_distance(instance)
    nv = solution.num_vehicles()
    served = solution.num_served_customers()
    logger.info(
        f"Nearest-Neighbor: {nv} vehículos, distancia={dist:.2f}, "
        f"clientes servidos={served}/{instance.num_customers}"
    )
    return solution
