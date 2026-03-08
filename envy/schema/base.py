from pydantic import BaseModel, Field

from uuid import uuid4, UUID


class Message(BaseModel):
    """The base class of anything sent over a socket."""

    uuid: UUID = Field(default_factory=uuid4, frozen=True)
