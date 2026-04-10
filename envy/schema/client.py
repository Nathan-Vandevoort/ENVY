import enum

from pydantic import BaseModel

from .job import Task


class ClientStatus(enum.Enum):
    IDLE = enum.auto()
    STOPPED = enum.auto()
    WORKING = enum.auto()


class ClientHeaders(BaseModel):
    username: str
    state: ClientStatus
    task: Task | None
