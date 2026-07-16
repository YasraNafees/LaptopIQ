import logging
import sys
from config import config


def setup_logger(name=__name__):
    logger = logging.getLogger(name)

    logger.setLevel(getattr(logging, config.LOG_LEVEL))

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File
    try:
        file_handler = logging.FileHandler(config.LOG_FILE, mode="a")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    except Exception as e:
        logger.error(f"Log file error: {e}")

    return logger


def get_logger(name=__name__):
    
    return setup_logger(name)