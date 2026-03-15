import abc
import asyncio
import logging
import queue
import uuid
from typing import Any
import dataclasses

from envy.api.data import RPCRequest
from envy.common.types import KeyedSet
from envy.schema import Message

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ClientConnection:
    name: str
    ip: str


@dataclasses.dataclass
class ConsoleConnection:
    name: str
    ip: str


class Server(abc.ABC):

    def __init__(self) -> None:
        self.running = False
        self.receive_queue = queue.Queue()
        self.send_queue = queue.Queue()

        self.clients = KeyedSet("name", ClientConnection)
        self.console = KeyedSet("name", ConsoleConnection)

        self._pending_requests: dict[uuid.UUID, asyncio.Future] = {}

    @abc.abstractmethod
    def start(self) -> None: ...

    @abc.abstractmethod
    def stop(self) -> None: ...

    async def send(self, message: RPCRequest) -> Any:
        """Send"""

        loop = asyncio.get_running_loop()
        future = loop.create_future()

        self._pending_requests[message.message_id] = future

        await self._send(message)

        response = await future

        if response.error:
            raise Exception(f"Server Error: {response.error}")

        return response.result

    @abc.abstractmethod
    async def _send(self, message: RPCRequest) -> None: ...

    @abc.abstractmethod
    def receive(self, data: Any) -> None:
        message = self._parse_message(data)
        self.receive_queue.put(message)

    @abc.abstractmethod
    def _parse_message(self, data: Any) -> Message: ...

    @abc.abstractmethod
    def register_client(self, connection: Any) -> ClientConnection:
        """Register a connection with the server. The connection gets added in self.clients."""

        ...

    @abc.abstractmethod
    def register_console(self, connection: Any) -> ConsoleConnection:
        """Register a connection with the server. The connection gets added in self.clients."""

        ...
