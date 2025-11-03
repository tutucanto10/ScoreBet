import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = "scorebet"):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # evita múltiplos handlers ao recarregar

    logger.setLevel(logging.INFO)
    fh = RotatingFileHandler(LOG_DIR / "app.log", maxBytes=2_000_000, backupCount=3)
    ch = logging.StreamHandler()

    fmt = logging.Formatter("[%(asctime)s] %(levelname)s - %(name)s - %(message)s")
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
