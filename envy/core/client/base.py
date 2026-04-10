import abc
import asyncio
import logging
import queue
import uuid
from typing import Any, Callable

from envy.api import RPCRequest, RPCResponse
from envy.api.exceptions import RPCError
from envy.api.server import RPCServer
from envy.common.types import Request

logger = logging.getLogger(__name__)


class Client(abc.ABC):

    def __init__(self) -> None:
        self.running = False
        self.receive_queue: queue.Queue[Request] = queue.Queue()
        self.send_queue: queue.Queue[RPCRequest | RPCResponse] = queue.Queue()

        self._pending_requests: dict[uuid.UUID, asyncio.Future] = {}

    @abc.abstractmethod
    def start(self) -> None: ...

    @abc.abstractmethod
    def stop(self) -> None: ...

    @abc.abstractmethod
    async def connect(self) -> RPCServer: ...

    async def send(self, message: RPCRequest | RPCResponse) -> Any:

        if isinstance(message, RPCRequest):
            loop = asyncio.get_running_loop()
            future = loop.create_future()

            self._pending_requests[message.message_id] = future
            await self._send(message)

            response = await future
            if response.error:
                raise response.error
            return response.result

        await self._send(message)

    @abc.abstractmethod
    async def _send(self, message: RPCRequest | RPCResponse) -> None: ...

    def receive(self, data: Any) -> None:
        message = self._parse_message(data)
        message_id = self._get_message_id(data)

        # A callable can never be recieved as a result. So data must represent a request.
        if isinstance(message, Callable):
            request = Request(func=message, message_id=message_id)
            self.receive_queue.put(request)
            return

        future = self._pending_requests[message_id]

        if isinstance(message, RPCError):
            future.set_exception(message)
            return

        future.set_result(message)

    @abc.abstractmethod
    def _parse_message(self, raw_data: Any) -> Callable | Any | RPCError: ...

    @abc.abstractmethod
    def _get_message_id(self, raw_data: Any) -> uuid.UUID: ...
