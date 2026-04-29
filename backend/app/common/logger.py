from __future__ import annotations
import logging
from pathlib import Path

def get_logger(name: str, logs_dir: str = "outputs/logs") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)

    file_handler = logging.FileHandler(Path(logs_dir) / "app.log", encoding="utf-8")
    file_handler.setFormatter(fmt)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger