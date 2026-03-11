"""Configuración de logging con loguru."""

import sys

from loguru import logger


def setup_logger(level: str = "INFO") -> None:
    """Configura loguru con el nivel especificado."""
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    )
    logger.add(
        "logs/macs_vrptw.log",
        level="DEBUG",
        rotation="10 MB",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function} - {message}",
    )
