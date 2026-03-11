"""Tests para el parser de instancias Solomon."""

import pytest

from src.parsers.solomon_parser import parse_bks_solution, parse_solomon_instance


@pytest.fixture
def instance():
    """Carga la instancia C208."""
    return parse_solomon_instance("data/c208.txt")


class TestSolomonParser:
    """Tests de parseo de instancia C208."""

    def test_instance_name(self, instance):
        assert instance.name == "C208"

    def test_num_customers(self, instance):
        assert instance.num_customers == 100

    def test_capacity(self, instance):
        assert instance.capacity == 700

    def test_depot(self, instance):
        assert instance.depot.id == 0
        assert instance.depot.x == 40
        assert instance.depot.y == 50
        assert instance.depot.demand == 0

    def test_depot_time_window(self, instance):
        assert instance.depot.ready_time == 0
        assert instance.depot.due_date == 3390

    def test_distance_matrix_shape(self, instance):
        n = instance.num_customers + 1
        assert instance.distance_matrix.shape == (n, n)

    def test_distance_symmetry(self, instance):
        for i in range(10):
            for j in range(i + 1, 10):
                assert abs(instance.distance(i, j) - instance.distance(j, i)) < 1e-10

    def test_distance_diagonal_zero(self, instance):
        for i in range(instance.num_customers + 1):
            assert instance.distance(i, i) == 0.0


class TestBKSSolution:
    """Tests de parseo y validación de la BKS."""

    def test_bks_num_routes(self):
        bks = parse_bks_solution("data/c208_bks.txt")
        assert bks.num_vehicles() == 3

    def test_bks_all_customers_served(self):
        instance = parse_solomon_instance("data/c208.txt")
        bks = parse_bks_solution("data/c208_bks.txt")
        served = bks.get_all_served_customers()
        expected = {c.id for c in instance.customers}
        assert served == expected

    def test_bks_distance(self):
        instance = parse_solomon_instance("data/c208.txt")
        bks = parse_bks_solution("data/c208_bks.txt")
        dist = bks.total_distance(instance)
        assert abs(dist - 588.32) < 0.5, f"BKS distancia={dist:.2f}, esperado ~588.32"

    def test_bks_feasible(self):
        instance = parse_solomon_instance("data/c208.txt")
        bks = parse_bks_solution("data/c208_bks.txt")
        assert bks.is_feasible(instance), "La BKS debe ser factible"
