"""Modelo de datos para una instancia VRPTW de Solomon."""

from dataclasses import dataclass, field
import math

import numpy as np

from src.models.customer import Customer


@dataclass
class Instance:
    """Representa una instancia completa del VRPTW.

    Atributos:
        name: Nombre de la instancia (e.g., 'C208').
        num_vehicles: Número máximo de vehículos disponibles.
        capacity: Capacidad de cada vehículo.
        depot: Nodo depósito (Customer con id=0).
        customers: Lista de clientes (sin depósito).
        distance_matrix: Matriz de distancias euclidianas precalculada.
    """

    name: str
    num_vehicles: int
    capacity: int
    depot: Customer
    customers: list[Customer]
    distance_matrix: np.ndarray = field(repr=False)

    @property
    def num_customers(self) -> int:
        """Número de clientes (sin contar el depósito)."""
        return len(self.customers)

    @property
    def all_nodes(self) -> list[Customer]:
        """Todos los nodos: depósito + clientes."""
        return [self.depot] + self.customers

    def distance(self, i: int, j: int) -> float:
        """Distancia euclidiana entre nodos i y j."""
        return float(self.distance_matrix[i, j])

    @staticmethod
    def compute_distance_matrix(nodes: list[Customer]) -> np.ndarray:
        """Calcula la matriz de distancias euclidianas con doble precisión."""
        n = len(nodes)
        matrix = np.zeros((n, n), dtype=np.float64)
        for i in range(n):
            for j in range(i + 1, n):
                dx = nodes[i].x - nodes[j].x
                dy = nodes[i].y - nodes[j].y
                dist = math.sqrt(dx * dx + dy * dy)
                matrix[i, j] = dist
                matrix[j, i] = dist
        return matrix
