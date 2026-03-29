import time

import pika

from src.core.logger import get_module_logger
from src.settings import settings

logger = get_module_logger(__name__)


def create_connection(max_retries: int = 10, delay: int = 1):
    creds = pika.PlainCredentials(settings.RABBIT_USER, settings.RABBIT_PASSWORD)

    for attempt in range(1, max_retries - 1):
        try:
            return pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=settings.RABBIT_HOST,
                    port=settings.RABBIT_PORT,
                    credentials=creds,
                    heartbeat=60,
                )
            )
        except Exception as e:
            logger.error(
                f"[rabbitmq] error connection attempr {attempt}/{max_retries} failed: {e}"
            )
            time.sleep(delay)

    raise RuntimeError("Could not connect to RabbitMq")
