from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Message(BaseModel):
    """The base class of anything sent over a socket."""

    message_id: UUID = Field(default_factory=uuid4)
