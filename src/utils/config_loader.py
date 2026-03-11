"""Carga y fusión de archivos de configuración YAML."""

from pathlib import Path
from typing import Any

import yaml


def _deep_merge(base: dict, override: dict) -> dict:
    """Fusiona recursivamente dos diccionarios, dando prioridad al override."""
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(
    default_path: str = "config/default.yaml",
    experiment_path: str | None = None,
) -> dict[str, Any]:
    """Carga configuración por defecto y opcionalmente fusiona con un experimento."""
    with open(default_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if experiment_path and Path(experiment_path).exists():
        with open(experiment_path, "r", encoding="utf-8") as f:
            experiment = yaml.safe_load(f)
        if experiment:
            config = _deep_merge(config, experiment)

    return config
