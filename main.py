"""Script principal de ejecución del algoritmo MACS-VRPTW."""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

from loguru import logger

from src.algorithm.local_search.cross_exchange import CrossExchange
from src.algorithm.local_search.or_opt import OrOpt
from src.algorithm.macs_vrptw import MACS_VRPTW
from src.evaluation.benchmark import compare_with_references
from src.evaluation.metrics import solution_summary
from src.evaluation.validator import validate_solution
from src.parsers.solomon_parser import parse_bks_solution, parse_solomon_instance
from src.utils.config_loader import load_config
from src.utils.logger import setup_logger
from src.utils.seed import set_global_seed


def run_single(config: dict, seed: int, run_id: int) -> dict:
    """Ejecuta una corrida del algoritmo y retorna resultados."""
    set_global_seed(seed)
    algo_cfg = config["algorithm"]

    # Parsear instancia
    instance = parse_solomon_instance(config["instance"]["path"])
    logger.info(f"Instancia: {instance.name}, {instance.num_customers} clientes, capacidad={instance.capacity}")

    # Búsqueda local: Or-opt (eficiente para rutas largas tipo C2)
    local_search = OrOpt()

    # Crear y ejecutar controlador
    macs = MACS_VRPTW(
        instance=instance,
        num_ants=algo_cfg["num_ants"],
        beta=algo_cfg["beta"],
        q0=algo_cfg["q0"],
        rho=algo_cfg["rho"],
        max_iterations=algo_cfg["max_iterations"],
        max_no_improvement=algo_cfg["max_no_improvement"],
        local_search=local_search,
    )

    start = time.time()
    solution = macs.solve()
    elapsed = time.time() - start

    # Validar solución
    is_feasible, messages = validate_solution(solution, instance)
    logger.info(f"Factibilidad: {is_feasible}")
    for msg in messages:
        logger.debug(msg)

    # Métricas y comparación
    summary = solution_summary(solution, instance)
    comparison = compare_with_references(solution, instance)

    result = {
        "run_id": run_id,
        "seed": seed,
        "timestamp": datetime.now().isoformat(),
        "instance": instance.name,
        "parameters": algo_cfg,
        "elapsed_seconds": round(elapsed, 2),
        "solution": summary,
        "comparison": comparison,
        "history": macs.history,
        "feasible": is_feasible,
    }

    logger.info(
        f"Run {run_id}: {summary['num_vehicles']} vehículos, "
        f"distancia={summary['total_distance']}, "
        f"gap_vs_bks={comparison['vs_bks']['gap_distance_pct']}%, "
        f"tiempo={elapsed:.1f}s"
    )

    return result


def validate_bks(config: dict) -> None:
    """Valida la BKS cargada contra la instancia."""
    instance = parse_solomon_instance(config["instance"]["path"])
    bks = parse_bks_solution(config["instance"]["bks_path"])

    dist = bks.total_distance(instance)
    is_feasible, messages = validate_solution(bks, instance)

    logger.info(f"BKS: {bks.num_vehicles()} vehículos, distancia={dist:.2f}")
    logger.info(f"BKS factible: {is_feasible}")
    for msg in messages:
        logger.debug(msg)


def main() -> None:
    """Punto de entrada principal."""
    # Cargar configuración
    config = load_config(
        default_path="config/default.yaml",
        experiment_path="config/experiments/c208.yaml",
    )

    setup_logger(config["execution"]["log_level"])

    # Crear directorio de resultados
    results_dir = Path(config["execution"]["results_dir"])
    results_dir.mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    # Validar BKS
    logger.info("=== Validación de BKS ===")
    validate_bks(config)

    # Ejecutar múltiples corridas
    num_runs = config["execution"]["num_runs"]
    base_seed = config["execution"]["seed"]
    all_results = []

    for run_id in range(1, num_runs + 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"=== CORRIDA {run_id}/{num_runs} (seed={base_seed + run_id - 1}) ===")
        logger.info(f"{'='*60}")

        result = run_single(config, seed=base_seed + run_id - 1, run_id=run_id)
        all_results.append(result)

        # Guardar resultado individual
        out_path = results_dir / f"run_{run_id}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"Resultado guardado en {out_path}")

    # Guardar resumen
    summary = {
        "instance": config["instance"]["path"],
        "num_runs": num_runs,
        "timestamp": datetime.now().isoformat(),
        "results": [
            {
                "run_id": r["run_id"],
                "seed": r["seed"],
                "vehicles": r["solution"]["num_vehicles"],
                "distance": r["solution"]["total_distance"],
                "feasible": r["feasible"],
                "elapsed": r["elapsed_seconds"],
            }
            for r in all_results
        ],
        "best": min(
            all_results,
            key=lambda r: (r["solution"]["num_vehicles"], r["solution"]["total_distance"]),
        )["solution"],
    }

    summary_path = results_dir / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Tabla resumen
    logger.info("\n=== RESUMEN DE RESULTADOS ===")
    logger.info(f"{'Run':>4} {'Seed':>6} {'Veh':>4} {'Distancia':>10} {'Factible':>9} {'Tiempo':>8}")
    for r in all_results:
        s = r["solution"]
        logger.info(
            f"{r['run_id']:>4} {r['seed']:>6} {s['num_vehicles']:>4} "
            f"{s['total_distance']:>10.2f} {'Sí' if r['feasible'] else 'No':>9} "
            f"{r['elapsed_seconds']:>7.1f}s"
        )

    logger.info(f"\nMejor solución: {summary['best']['num_vehicles']} veh, {summary['best']['total_distance']} dist")


if __name__ == "__main__":
    main()
