from typing import TypeVar

import pika
from pydantic import BaseModel

from src.events.connection import create_connection
from src.events.schemas import PrimaryEvent, SecondaryEvent
from src.events.queues import Queues

T = TypeVar("T", bound=BaseModel)

def send_event(message: T) -> None:
    connection = create_connection()
    channel = connection.channel()

    channel.queue_declare(
        queue= Queues.MATCH_REQUESTS,
        durable=True
    )

    body = message.model_dump_json().encode('utf-8')

    channel.basic_publish(
        exchange='',
        routing_key=Queues.MATCH_REQUESTS,
        body=body,
        properties=pika.BasicProperties(
            delivery_mode=2,
            content_type="application/json",
        )
    )
    connection.close()


if __name__ == "__main__":
    primary_event = PrimaryEvent(
        event_type='primary',
        value='Hello'
    )
    secondary_event = SecondaryEvent(
        event_type='secondary',
        value='World'
    )
    send_event(message=primary_event)
    send_event(message=secondary_event)


    