"""Parser para instancias Solomon y soluciones BKS del VRPTW."""

from pathlib import Path

from src.models.customer import Customer
from src.models.instance import Instance
from src.models.solution import Route, Solution


def parse_solomon_instance(filepath: str | Path) -> Instance:
    """Lee un archivo de instancia Solomon y retorna un objeto Instance.

    Formato esperado:
        Línea 1: Nombre
        Líneas 2-4: VEHICLE / NUMBER CAPACITY / <num> <cap>
        Línea 5+: CUSTOMER / headers / datos
    """
    filepath = Path(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    name = lines[0]

    # Buscar la línea con exactamente 2 números (num_vehicles, capacity)
    num_vehicles = 0
    capacity = 0
    for line in lines[1:]:
        parts = line.split()
        if len(parts) == 2:
            try:
                num_vehicles = int(parts[0])
                capacity = int(parts[1])
                break
            except ValueError:
                continue

    # Parsear clientes — buscar líneas que empiecen con un número
    nodes: list[Customer] = []
    for line in lines:
        tokens = line.split()
        if len(tokens) == 7:
            try:
                cid = int(tokens[0])
                x = float(tokens[1])
                y = float(tokens[2])
                demand = int(tokens[3])
                ready = int(tokens[4])
                due = int(tokens[5])
                service = int(tokens[6])
                nodes.append(Customer(cid, x, y, demand, ready, due, service))
            except ValueError:
                continue

    depot = nodes[0]
    customers = nodes[1:]

    distance_matrix = Instance.compute_distance_matrix(nodes)

    return Instance(
        name=name,
        num_vehicles=num_vehicles,
        capacity=capacity,
        depot=depot,
        customers=customers,
        distance_matrix=distance_matrix,
    )


def parse_bks_solution(filepath: str | Path) -> Solution:
    """Lee un archivo de solución BKS y retorna un objeto Solution.

    Formato esperado:
        Route N : id1 id2 id3 ...
    """
    filepath = Path(filepath)
    routes: list[Route] = []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.lower().startswith("route"):
                # Extraer la parte después de ':'
                parts = line.split(":")
                if len(parts) >= 2:
                    customer_ids = [int(x) for x in parts[1].split()]
                    routes.append(Route(customer_ids=customer_ids))

    return Solution(routes=routes)
