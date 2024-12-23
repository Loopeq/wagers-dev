import logging
from colorlog import ColoredFormatter

logger = logging.getLogger()
logger.setLevel(logging.INFO)


handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter(
    '%(log_color)s%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
))
logger.addHandler(handler)
logger.propagate = False
