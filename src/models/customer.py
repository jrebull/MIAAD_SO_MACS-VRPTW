"""Modelo de datos para clientes (nodos) del VRPTW."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Customer:
    """Representa un cliente o el depósito en una instancia VRPTW.

    Atributos:
        id: Identificador del nodo (0 = depósito).
        x: Coordenada X.
        y: Coordenada Y.
        demand: Demanda del cliente.
        ready_time: Inicio de la ventana de tiempo.
        due_date: Fin de la ventana de tiempo.
        service_time: Tiempo de servicio en el nodo.
    """

    id: int
    x: float
    y: float
    demand: int
    ready_time: int
    due_date: int
    service_time: int

    @property
    def is_depot(self) -> bool:
        """Retorna True si este nodo es el depósito."""
        return self.id == 0
