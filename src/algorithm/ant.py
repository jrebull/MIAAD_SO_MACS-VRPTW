"""Procedimiento constructivo new_active_ant (Figure 6 del artículo)."""

import random

import numpy as np

from src.models.instance import Instance
from src.models.solution import Route, Solution
from src.algorithm.pheromone import PheromoneMatrix


def new_active_ant(
    ant_id: int,
    instance: Instance,
    pheromone: PheromoneMatrix,
    beta: float,
    q0: float,
    rho: float,
    num_vehicles: int,
    in_vector: np.ndarray | None = None,
    apply_local_search: bool = False,
    local_search_fn=None,
) -> Solution:
    """Construye una solución usando el procedimiento new_active_ant.

    Implementa el modelo de depósitos duplicados (Section 5.4.2):
    el depósito se duplica tantas veces como vehículos disponibles.
    Cada hormiga construye un único tour que pasa por clientes y
    depósitos duplicados, transformando el VRP en un TSP.

    Args:
        ant_id: Identificador de la hormiga.
        instance: Instancia VRPTW.
        pheromone: Matriz de feromonas compartida.
        beta: Peso de la información heurística.
        q0: Probabilidad de explotación.
        rho: Tasa de evaporación (para actualización local).
        num_vehicles: Número de vehículos (depósitos duplicados).
        in_vector: Vector IN para ACS-VEI (None o ceros para ACS-TIME).
        apply_local_search: Si True, aplica búsqueda local a solución factible.
        local_search_fn: Función de búsqueda local (callable).

    Returns:
        Solución construida por la hormiga.
    """
    n = instance.num_customers
    use_in = in_vector is not None and np.any(in_vector > 0)

    # Inicializar estado
    unvisited_customers = set(c.id for c in instance.customers)
    depot_copies_remaining = num_vehicles

    # Construir rutas
    routes: list[list[int]] = []
    current_route: list[int] = []
    current_time = 0.0
    current_load = 0
    current_node = 0  # Empieza en el depósito
    depot_copies_remaining -= 1  # Usamos una copia del depósito para empezar

    while True:
        # Calcular nodos factibles
        feasible = _get_feasible_nodes(
            current_node, current_time, current_load,
            unvisited_customers, instance, depot_copies_remaining,
        )

        if not feasible:
            # No hay nodos factibles -> finalizar ruta actual y terminar
            if current_route:
                routes.append(current_route)
            break

        # Calcular eta (atractivo heurístico) para cada nodo factible
        etas = {}
        for j in feasible:
            etas[j] = _compute_eta(
                current_node, j, current_time, instance, in_vector
            )

        # Regla de transición de estado (Eq. 1)
        next_node = _state_transition_rule(
            current_node, feasible, etas, pheromone, beta, q0
        )

        if next_node == 0:
            # Ir a un depósito duplicado -> cerrar ruta actual, abrir nueva
            if current_route:
                routes.append(current_route)
            current_route = []
            current_time = 0.0
            current_load = 0
            current_node = 0
            depot_copies_remaining -= 1
        else:
            # Visitar cliente
            customer = instance.all_nodes[next_node]
            travel = instance.distance(current_node, next_node)
            arrival = current_time + travel
            current_time = max(arrival, customer.ready_time) + customer.service_time
            current_load += customer.demand
            current_route.append(next_node)
            unvisited_customers.discard(next_node)
            current_node = next_node

        # Actualización local de feromonas (Eq. 3)
        prev = 0 if (next_node == 0 or not current_route) else (
            current_route[-2] if len(current_route) >= 2 else 0
        )
        actual_prev = 0 if next_node == 0 else (
            current_route[-2] if len(current_route) >= 2 else 0
        )
        pheromone.local_update(actual_prev, next_node, rho)

    # Procedimiento de inserción: insertar clientes no visitados
    solution = Solution(routes=[Route(customer_ids=r) for r in routes])
    if unvisited_customers:
        solution = _insertion_procedure(solution, unvisited_customers, instance)

    # Búsqueda local (solo si se requiere y la solución es factible)
    if apply_local_search and local_search_fn and solution.is_feasible(instance):
        solution = local_search_fn(solution, instance)

    return solution


def _get_feasible_nodes(
    current_node: int,
    current_time: float,
    current_load: int,
    unvisited: set[int],
    instance: Instance,
    depot_copies_remaining: int,
) -> list[int]:
    """Calcula el conjunto de nodos factibles desde la posición actual."""
    feasible = []

    for cid in unvisited:
        customer = instance.all_nodes[cid]
        travel = instance.distance(current_node, cid)
        arrival = current_time + travel
        start_service = max(arrival, customer.ready_time)

        # Verificar ventana de tiempo
        if start_service > customer.due_date:
            continue

        # Verificar capacidad
        if current_load + customer.demand > instance.capacity:
            continue

        # Verificar que pueda regresar al depósito a tiempo
        return_time = start_service + customer.service_time + instance.distance(cid, 0)
        if return_time > instance.depot.due_date:
            continue

        feasible.append(cid)

    # Agregar depósito duplicado si hay copias restantes y hay ruta actual
    if depot_copies_remaining > 0 and current_node != 0:
        feasible.append(0)

    return feasible


def _compute_eta(
    i: int,
    j: int,
    current_time: float,
    instance: Instance,
    in_vector: np.ndarray | None,
) -> float:
    """Calcula el atractivo heurístico eta_ij (del pseudocódigo new_active_ant).

    delivery_time_j = max(current_time + t_ij, b_j)
    delta_time_ij = delivery_time_j - current_time
    distance_ij = delta_time_ij * (e_j - current_time)
    distance_ij = max(1.0, distance_ij - IN_j)
    eta_ij = 1.0 / distance_ij
    """
    if j == 0:
        # Para el depósito, usar solo la distancia
        dist = instance.distance(i, j)
        return 1.0 / max(1.0, dist)

    customer_j = instance.all_nodes[j]
    t_ij = instance.distance(i, j)
    b_j = customer_j.ready_time
    e_j = customer_j.due_date

    delivery_time_j = max(current_time + t_ij, b_j)
    delta_time_ij = delivery_time_j - current_time
    distance_ij = delta_time_ij * (e_j - current_time)
    distance_ij = max(1.0, distance_ij)

    # Aplicar penalización IN (solo ACS-VEI)
    if in_vector is not None and j > 0:
        in_j = float(in_vector[j])
        distance_ij = max(1.0, distance_ij - in_j)

    return 1.0 / distance_ij


def _state_transition_rule(
    current: int,
    feasible: list[int],
    etas: dict[int, float],
    pheromone: PheromoneMatrix,
    beta: float,
    q0: float,
) -> int:
    """Regla de transición de estado ACS (Eq. 1).

    Con probabilidad q0: explotación (argmax).
    Con probabilidad 1-q0: exploración (ruleta).
    """
    if not feasible:
        return 0

    if len(feasible) == 1:
        return feasible[0]

    # Calcular tau * eta^beta para cada nodo factible
    scores = {}
    for j in feasible:
        tau = pheromone.get(current, j)
        eta = etas.get(j, 1e-10)
        scores[j] = tau * (eta ** beta)

    q = random.random()

    if q <= q0:
        # Explotación: elegir el mejor
        return max(scores, key=scores.get)
    else:
        # Exploración: selección por ruleta
        total = sum(scores.values())
        if total <= 0:
            return random.choice(feasible)

        r = random.random() * total
        cumulative = 0.0
        for j in feasible:
            cumulative += scores[j]
            if cumulative >= r:
                return j
        return feasible[-1]


def _insertion_procedure(
    solution: Solution,
    unvisited: set[int],
    instance: Instance,
) -> Solution:
    """Procedimiento de inserción (Section 5.4.3).

    Ordena clientes no visitados por demanda decreciente e intenta
    insertarlos en la mejor posición factible.
    """
    # Ordenar por demanda decreciente
    sorted_unvisited = sorted(
        unvisited,
        key=lambda cid: instance.all_nodes[cid].demand,
        reverse=True,
    )

    for cid in sorted_unvisited:
        best_route_idx = -1
        best_position = -1
        best_cost_increase = float("inf")

        for r_idx, route in enumerate(solution.routes):
            if not route.customer_ids:
                continue

            for pos in range(len(route.customer_ids) + 1):
                # Intentar insertar cid en la posición pos
                new_ids = route.customer_ids[:pos] + [cid] + route.customer_ids[pos:]
                test_route = Route(customer_ids=new_ids)

                if not test_route.is_feasible(instance):
                    continue

                cost_increase = (
                    test_route.total_distance(instance)
                    - route.total_distance(instance)
                )
                if cost_increase < best_cost_increase:
                    best_cost_increase = cost_increase
                    best_route_idx = r_idx
                    best_position = pos

        if best_route_idx >= 0:
            solution.routes[best_route_idx].customer_ids.insert(
                best_position, cid
            )

    return solution
