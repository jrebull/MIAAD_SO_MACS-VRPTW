"""Comparación contra BKS y resultados del artículo original."""

from src.evaluation.metrics import compute_gap
from src.models.instance import Instance
from src.models.solution import Solution

# Resultados del artículo para C208 (Gambardella et al., 1999)
PAPER_RESULTS_C208 = {
    "table1": {"vehicles": 3.00, "distance": 592.97},
    "table2_best": {"vehicles": 3.00, "distance": 589.86},
}

BKS_C208 = {
    "vehicles": 3,
    "distance": 588.32,
    "authors": "Geir Hasle, Oddvar Kloster",
    "date": "29.12.2003",
}


def compare_with_references(
    solution: Solution, instance: Instance
) -> dict:
    """Compara una solución contra el artículo original y la BKS."""
    our_dist = solution.total_distance(instance)
    our_veh = solution.num_vehicles()

    return {
        "our_result": {
            "vehicles": our_veh,
            "distance": round(our_dist, 2),
        },
        "vs_paper_table1": {
            "gap_vehicles": our_veh - PAPER_RESULTS_C208["table1"]["vehicles"],
            "gap_distance_pct": round(
                compute_gap(our_dist, PAPER_RESULTS_C208["table1"]["distance"]), 2
            ),
        },
        "vs_paper_table2": {
            "gap_vehicles": our_veh - PAPER_RESULTS_C208["table2_best"]["vehicles"],
            "gap_distance_pct": round(
                compute_gap(our_dist, PAPER_RESULTS_C208["table2_best"]["distance"]), 2
            ),
        },
        "vs_bks": {
            "gap_vehicles": our_veh - BKS_C208["vehicles"],
            "gap_distance_pct": round(
                compute_gap(our_dist, BKS_C208["distance"]), 2
            ),
        },
        "paper_results": PAPER_RESULTS_C208,
        "bks": BKS_C208,
    }
