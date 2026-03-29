from pydantic import BaseModel, TypeAdapter, Field
from typing import Literal, Annotated

class PrimaryEvent(BaseModel):
    event_type: Literal["primary"]
    value: str

class SecondaryEvent(BaseModel):
    event_type: Literal["secondary"]
    value: str


IncomingEvent = Annotated[
    PrimaryEvent | SecondaryEvent,
    Field(discriminator="event_type"),
]

incoming_event_adapter = TypeAdapter(IncomingEvent)