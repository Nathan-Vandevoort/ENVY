import asyncio
import dataclasses
import logging
from typing import Any, Queue

from websockets.asyncio import server

from envy.api.server.api import RPCRequest, RPCResponse

from .base import ClientConnection, ConsoleConnection, Server
from envy.schema import Message

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class WebsocketClientConnection(ClientConnection):
    socket: server.ServerConnection


@dataclasses.dataclass
class WebsocketConsoleConnection(ConsoleConnection):
    socket: server.ServerConnection


class WebsocketServer(Server):


    def start(self) -> None:
        self.running = True

        asyncio.run(self._start())

        self.running = False

    async def _send(self, message: RPCRequest) -> None:
                


    async def _start(self) -> None:
        async with server.serve(self._handler, "", 8001) as s:
            await s.serve_forever()

    async def _handler(self, connection: server.ServerConnection) -> None:
        if not self._validate_connection(connection):
            logger.info(f"Refused connection from {connection.remote_address!r}")
            return

        assert connection.request is not None

        if connection.request.path == "/client":
            client = self.register_client(connection)
            consumer_task = asyncio.create_task(self._client_consumer(client))
            producer_task = asyncio.create_task(self._client_producer(client))
            done, pending = await asyncio.wait(
                [consumer_task, producer_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()

        elif connection.request.path == "/console":
            self.register_console(connection)

        else:
            raise ValueError(f"recieved connection has an unknown path {connection.request.path!r}")

    async def _client_consumer(self, client: WebsocketClientConnection) -> None:
        async for raw_data in client.socket:
            message = self._parse_message(raw_data)
            if message:
                self.receive_queue.put(message)

    async def _client_producer(self, client: WebsocketClientConnection) -> None:
        while True:
            if not self.send_queue.empty():
                message = self.send_queue.get(block=False)
                await client.socket.send(message.model_dump_json())

    def _parse_message(self, raw_message: str) -> RPCRequest | RPCResponse:

        # Parse RPCResponse.
        pass
        

    def _validate_connection(self, connection: server.ServerConnection) -> bool:

        if not connection.request or not connection.request.headers:
            logger.debug(f"connection is not valid because it has no headers")
            return False

        if connection.request.path not in ("/client", "/console"):
            logger.debug(f"connection is not valid because the path {connection.request.path!r} is not valid")
            return False

        name = connection.request.headers.get("name")
        if not name:
            logger.debug(f"connection is not valid because a client name was not provided in the header")
            return False

        if name in (client.name for client in self.clients):
            logger.debug(f"connection is not valid because a client with the same name is already connected")
            return False

        return True

    def register_client(self, connection: server.ServerConnection) -> WebsocketClientConnection:

        # _validate_connection should have already checked all this. If an error is thrown here that means that method has a bug.
        assert connection.request is not None
        name = connection.request.headers["name"]

        # An assumption is made here the connection is using ipv4
        ip, _ = connection.remote_address[0]

        new_client = WebsocketClientConnection(socket=connection, name=name, ip=ip)
        self.clients.add(new_client)

        return new_client
