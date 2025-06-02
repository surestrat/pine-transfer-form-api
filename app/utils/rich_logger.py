from rich.logging import RichHandler
import logging
import sys


def setup_rich_logging(level=logging.INFO):
    """
    Sets up logging with RichHandler for pretty console output.
    Call this early in your app (e.g. main.py or __init__.py).
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[RichHandler(rich_tracebacks=True, show_time=False, show_level=True, show_path=True)],
        force=True,
    )


def get_rich_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance with the given name, using RichHandler.
    """
    return logging.getLogger(name)

