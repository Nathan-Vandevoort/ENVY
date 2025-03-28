import dataclasses
from enum import Enum

from websockets.server import WebSocketServerProtocol


class ClientStatus(Enum):
    IDLE = 'IDLE'
    WORKING = 'WORKING'
    STOPPED = 'STOPPED'


@dataclasses.dataclass
class Client:
    name: str
    status: ClientStatus
    job_id: int | None = None
    task_id: int | None = None
    ip: str | None = None
    socket: WebSocketServerProtocol | None = None


@dataclasses.dataclass
class Console:
    ip: str
    socket: WebSocketServerProtocol
