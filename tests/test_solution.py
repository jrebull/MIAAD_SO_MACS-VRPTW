"""Tests para el modelo de soluciones y validación."""

import pytest

from src.models.solution import Route, Solution
from src.parsers.solomon_parser import parse_solomon_instance


@pytest.fixture
def instance():
    """Carga la instancia C208."""
    return parse_solomon_instance("data/c208.txt")


class TestRoute:
    """Tests para rutas individuales."""

    def test_empty_route(self, instance):
        route = Route(customer_ids=[])
        assert route.total_distance(instance) == 0.0
        assert route.is_feasible(instance)

    def test_single_customer_route(self, instance):
        route = Route(customer_ids=[1])
        assert route.total_distance(instance) > 0
        assert route.is_feasible(instance)

    def test_route_demand(self, instance):
        route = Route(customer_ids=[1, 2])
        demand = route.total_demand(instance)
        expected = instance.all_nodes[1].demand + instance.all_nodes[2].demand
        assert demand == expected


class TestSolution:
    """Tests para soluciones completas."""

    def test_empty_solution(self, instance):
        sol = Solution(routes=[])
        assert sol.num_vehicles() == 0
        assert sol.total_distance(instance) == 0.0

    def test_solution_copy(self, instance):
        sol = Solution(routes=[Route(customer_ids=[1, 2])])
        copy = sol.copy()
        copy.routes[0].customer_ids.append(3)
        assert len(sol.routes[0].customer_ids) == 2
        assert len(copy.routes[0].customer_ids) == 3
