"""Métricas de evaluación para soluciones VRPTW."""

from src.models.instance import Instance
from src.models.solution import Solution


def compute_gap(our_value: float, reference_value: float) -> float:
    """Calcula el porcentaje de gap respecto a un valor de referencia."""
    if reference_value == 0:
        return 0.0
    return ((our_value - reference_value) / reference_value) * 100.0


def solution_summary(solution: Solution, instance: Instance) -> dict:
    """Genera un resumen de métricas de la solución."""
    total_dist = solution.total_distance(instance)
    num_veh = solution.num_vehicles()
    num_served = solution.num_served_customers()

    route_details = []
    for i, route in enumerate(solution.routes):
        if route.customer_ids:
            route_details.append({
                "route_id": i + 1,
                "num_customers": len(route),
                "distance": round(route.total_distance(instance), 2),
                "demand": route.total_demand(instance),
                "customers": route.customer_ids,
            })

    return {
        "num_vehicles": num_veh,
        "total_distance": round(total_dist, 2),
        "num_served_customers": num_served,
        "is_feasible": solution.is_feasible(instance),
        "routes": route_details,
    }
