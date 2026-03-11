"""Modelo de datos para rutas y soluciones del VRPTW."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field

from src.models.instance import Instance


@dataclass
class Route:
    """Representa una ruta individual (secuencia de clientes visitados por un vehículo).

    La ruta NO incluye el depósito explícitamente en la lista; se asume
    que inicia y termina en el depósito (nodo 0).
    """

    customer_ids: list[int] = field(default_factory=list)

    def total_distance(self, instance: Instance) -> float:
        """Calcula la distancia total de la ruta incluyendo ida y vuelta al depósito."""
        if not self.customer_ids:
            return 0.0
        dist = instance.distance(0, self.customer_ids[0])
        for i in range(len(self.customer_ids) - 1):
            dist += instance.distance(self.customer_ids[i], self.customer_ids[i + 1])
        dist += instance.distance(self.customer_ids[-1], 0)
        return dist

    def total_demand(self, instance: Instance) -> int:
        """Calcula la demanda total de la ruta."""
        return sum(instance.all_nodes[c].demand for c in self.customer_ids)

    def is_feasible(self, instance: Instance) -> bool:
        """Verifica factibilidad de capacidad y ventanas de tiempo."""
        if not self.customer_ids:
            return True

        load = 0
        current_time = 0.0

        for i, cid in enumerate(self.customer_ids):
            customer = instance.all_nodes[cid]
            prev_id = 0 if i == 0 else self.customer_ids[i - 1]
            travel_time = instance.distance(prev_id, cid)
            current_time += travel_time

            # Esperar si se llega antes de la ventana
            if current_time < customer.ready_time:
                current_time = float(customer.ready_time)

            # Verificar que no se pase de la ventana
            if current_time > customer.due_date:
                return False

            current_time += customer.service_time
            load += customer.demand

            if load > instance.capacity:
                return False

        # Verificar regreso al depósito dentro de su ventana
        last_cid = self.customer_ids[-1]
        return_time = current_time + instance.distance(last_cid, 0)
        if return_time > instance.depot.due_date:
            return False

        return True

    def __len__(self) -> int:
        return len(self.customer_ids)


@dataclass
class Solution:
    """Representa una solución completa del VRPTW (conjunto de rutas)."""

    routes: list[Route] = field(default_factory=list)

    def total_distance(self, instance: Instance) -> float:
        """Distancia total de todas las rutas."""
        return sum(r.total_distance(instance) for r in self.routes)

    def num_vehicles(self) -> int:
        """Número de vehículos usados (rutas no vacías)."""
        return sum(1 for r in self.routes if r.customer_ids)

    def num_served_customers(self) -> int:
        """Número total de clientes servidos."""
        return sum(len(r) for r in self.routes)

    def is_feasible(self, instance: Instance) -> bool:
        """Verifica factibilidad completa: capacidad, TW y cobertura."""
        served = set()
        for route in self.routes:
            if not route.is_feasible(instance):
                return False
            for cid in route.customer_ids:
                if cid in served:
                    return False  # Cliente duplicado
                served.add(cid)

        # Verificar que todos los clientes estén servidos
        expected = {c.id for c in instance.customers}
        return served == expected

    def get_all_served_customers(self) -> set[int]:
        """Retorna el conjunto de IDs de clientes servidos."""
        served = set()
        for route in self.routes:
            served.update(route.customer_ids)
        return served

    def copy(self) -> Solution:
        """Retorna una copia profunda de la solución."""
        return deepcopy(self)

    def __str__(self) -> str:
        lines = [f"Solución: {self.num_vehicles()} vehículos"]
        for i, route in enumerate(self.routes):
            if route.customer_ids:
                seq = " -> ".join(str(c) for c in route.customer_ids)
                lines.append(f"  Ruta {i + 1}: 0 -> {seq} -> 0")
        return "\n".join(lines)
