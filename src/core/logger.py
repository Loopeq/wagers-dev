import logging
from logging.handlers import RotatingFileHandler
import os

def get_module_logger(mod_name, log_file='logs/errors.log'):
    """
    To use this:
        logger = get_module_logger(__name__, log_file="app.log")
    """
    logger = logging.getLogger(mod_name)
    logger.setLevel(logging.ERROR)

    if logger.handlers:
        return logger

    stream_handler = logging.StreamHandler()
    stream_formatter = logging.Formatter(
        '%(asctime)s [%(name)-6s] %(levelname)-8s %(message)s'
    )
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=20 * 1024 * 1024, backupCount=5, encoding='utf-8'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s [%(name)-6s] %(levelname)-8s %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
