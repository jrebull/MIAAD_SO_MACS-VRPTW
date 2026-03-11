"""Tests para la matriz de feromonas."""

import pytest

from src.algorithm.pheromone import PheromoneMatrix
from src.models.solution import Route, Solution
from src.parsers.solomon_parser import parse_solomon_instance


@pytest.fixture
def instance():
    return parse_solomon_instance("data/c208.txt")


class TestPheromoneMatrix:
    """Tests para PheromoneMatrix."""

    def test_initialization(self):
        pm = PheromoneMatrix(10, tau_0=0.5)
        assert pm.get(0, 1) == 0.5
        assert pm.get(5, 9) == 0.5

    def test_local_update(self):
        pm = PheromoneMatrix(10, tau_0=0.5)
        pm.local_update(0, 1, rho=0.1)
        expected = (1 - 0.1) * 0.5 + 0.1 * 0.5
        assert abs(pm.get(0, 1) - expected) < 1e-10

    def test_local_update_symmetry(self):
        pm = PheromoneMatrix(10, tau_0=0.5)
        pm.local_update(0, 1, rho=0.1)
        assert abs(pm.get(0, 1) - pm.get(1, 0)) < 1e-10

    def test_global_update(self, instance):
        pm = PheromoneMatrix(101, tau_0=0.01)
        sol = Solution(routes=[Route(customer_ids=[1, 2, 3])])
        old_val = pm.get(0, 1)
        pm.global_update(sol, rho=0.1, instance=instance)
        assert pm.get(0, 1) != old_val

    def test_reinitialize(self):
        pm = PheromoneMatrix(10, tau_0=0.5)
        pm.local_update(0, 1, rho=0.1)
        pm.reinitialize(1.0)
        assert pm.get(0, 1) == 1.0
