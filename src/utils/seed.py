"""Control de semillas para reproducibilidad."""

import random

import numpy as np


def set_global_seed(seed: int) -> None:
    """Establece la semilla global para random y numpy."""
    random.seed(seed)
    np.random.seed(seed)
