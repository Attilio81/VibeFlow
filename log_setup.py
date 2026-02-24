import logging
from logging.handlers import RotatingFileHandler


def setup_logging(log_file: str = "vibeflow.log") -> logging.Logger:
    """Configure application-wide logging to both file and console.

    File: DEBUG level, rotating (5 MB max, 3 backups).
    Console: INFO level.
    """
    logger = logging.getLogger("vibeflow")
    if logger.handlers:
        return logger  # Already configured – avoid duplicate handlers

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler
    fh = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
