import dataclasses
from enum import Enum

from websockets.server import WebSocketServerProtocol


class ClientStatus(Enum):
    IDLE = 'IDLE'
    WORKING = 'WORKING'
    STOPPED = 'STOPPED'


@dataclasses.dataclass
class Client:
    ip: str
    socket: WebSocketServerProtocol
    status: ClientStatus
    job: int | None
    task: int | None


@dataclasses.dataclass
class ClientState:
    name: str
    connected: bool = False
    status: ClientStatus = ClientStatus.IDLE
    job_id: int | None = None
    task_id: int | None = None
