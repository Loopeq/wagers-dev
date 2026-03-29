from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar, cast

from pydantic import BaseModel

from src.core.logger import get_module_logger
from src.events.schemas import PrimaryEvent, SecondaryEvent

logger = get_module_logger(__name__)

T = TypeVar("T", bound=BaseModel)

_HANDLERS: dict[type[BaseModel], Callable[[BaseModel], None]] = {}

def register_handler(model: type[T]) -> Callable[[Callable[[T], None]], Callable[[T], None]]:

    def decorator(func: Callable[[T], None]) -> Callable[[T], None]:
        _HANDLERS[model] = cast(Callable[[BaseModel], None], func)
        return func

    return decorator


@register_handler(PrimaryEvent)
def handle_test(event: PrimaryEvent) -> None:
    logger.error("[handler] Test event received: value=%s", event.event_type)


@register_handler(SecondaryEvent)
def handle_user_created(event: SecondaryEvent) -> None:
    logger.error(
        "[handler] User created: user_id=%s email=%s",
        event.event_type,
        event.event_type,
    )


def handle_event(event: BaseModel) -> None:
    handler = _HANDLERS.get(type(event))
    if handler is not None:
        handler(event)
        return

    for model, fallback_handler in _HANDLERS.items():
        if isinstance(event, model):
            fallback_handler(event)
            return

    raise ValueError(f"No handler registered for event type: {type(event).__name__}")