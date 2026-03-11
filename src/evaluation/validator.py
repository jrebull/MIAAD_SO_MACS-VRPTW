"""Validación de factibilidad de soluciones VRPTW."""

from loguru import logger

from src.models.instance import Instance
from src.models.solution import Route, Solution


def validate_route(route: Route, instance: Instance) -> tuple[bool, str]:
    """Valida una ruta individual. Retorna (es_factible, mensaje_detalle)."""
    if not route.customer_ids:
        return True, "Ruta vacía"

    load = 0
    current_time = 0.0

    for i, cid in enumerate(route.customer_ids):
        customer = instance.all_nodes[cid]
        prev_id = 0 if i == 0 else route.customer_ids[i - 1]
        travel_time = instance.distance(prev_id, cid)
        current_time += travel_time

        if current_time < customer.ready_time:
            current_time = float(customer.ready_time)

        if current_time > customer.due_date:
            return False, (
                f"Violación TW en cliente {cid}: llegada={current_time:.2f}, "
                f"due_date={customer.due_date}"
            )

        current_time += customer.service_time
        load += customer.demand

        if load > instance.capacity:
            return False, (
                f"Violación capacidad en cliente {cid}: carga={load}, "
                f"capacidad={instance.capacity}"
            )

    last_cid = route.customer_ids[-1]
    return_time = current_time + instance.distance(last_cid, 0)
    if return_time > instance.depot.due_date:
        return False, (
            f"Regreso tardío al depósito: {return_time:.2f} > "
            f"{instance.depot.due_date}"
        )

    return True, f"Factible: {len(route)} clientes, carga={load}, tiempo_retorno={return_time:.2f}"


def validate_solution(solution: Solution, instance: Instance) -> tuple[bool, list[str]]:
    """Valida una solución completa. Retorna (es_factible, lista_mensajes)."""
    messages: list[str] = []
    all_feasible = True

    for i, route in enumerate(solution.routes):
        if not route.customer_ids:
            continue
        feasible, msg = validate_route(route, instance)
        messages.append(f"Ruta {i + 1}: {msg}")
        if not feasible:
            all_feasible = False

    # Verificar cobertura
    served = solution.get_all_served_customers()
    expected = {c.id for c in instance.customers}
    missing = expected - served
    extra = served - expected

    if missing:
        all_feasible = False
        messages.append(f"Clientes no servidos: {sorted(missing)}")
    if extra:
        all_feasible = False
        messages.append(f"Clientes inválidos: {sorted(extra)}")

    # Verificar duplicados
    all_ids: list[int] = []
    for route in solution.routes:
        all_ids.extend(route.customer_ids)
    if len(all_ids) != len(set(all_ids)):
        all_feasible = False
        messages.append("Clientes duplicados detectados")

    return all_feasible, messages
