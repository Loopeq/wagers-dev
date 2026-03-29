from pydantic import ValidationError

from src.core.logger import get_module_logger
from src.events.connection import create_connection
from src.events.handler import handle_event
from src.events.schemas import incoming_event_adapter
from src.events.queues import Queues

logger = get_module_logger(__name__)

def receive_events() -> None:
    connection = create_connection()
    channel = connection.channel()

    channel.queue_declare(
        queue=Queues.MATCH_RESULTS,
        durable=True,
    )
    channel.basic_qos(prefetch_count=1)

    def callback(ch, method, _, body: bytes) -> None:
        try:
            event = incoming_event_adapter.validate_json(body)

            handle_event(event)

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except ValidationError as e:
            logger.error("[receiver] invalid message schema: %s", e)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            logger.exception("[receiver] failed to process message: %s", e)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(
        queue=Queues.MATCH_RESULTS,
        on_message_callback=callback,
    )

    try:
        channel.start_consuming()
    finally:
        try:
            if channel.is_open:
                channel.close()
        finally:
            if connection.is_open:
                connection.close()


if __name__ == "__main__":
    receive_events()