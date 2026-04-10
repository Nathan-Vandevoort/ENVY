import asyncio
import json
import logging
import socket
import uuid
from typing import Any, Callable

import websockets

from envy import utils
from envy.api import RPCRequest, RPCResponse
from envy.api.client import RPCClient
from envy.api.exceptions import RPCError
from envy.api.server.api import RPCServer
from envy.common import constants
from envy.schema.client import ClientHeaders, ClientStatus

from .base import Client

logger = logging.getLogger(__name__)


class WebsocketRPCServer(RPCServer):

    def __init__(self, client: Client, name: str, ip: str, websocket: websockets.ClientConnection) -> None:
        super().__init__(client, name, ip)

        self.socket = websocket


class WebsocketClient(Client):

    def __init__(self) -> None:
        self.status = ClientStatus.IDLE

        super().__init__()

    async def connect(self) -> WebsocketRPCServer:
        server = get_server()
        uri = f"ws://{server}:{constants.PORT}/client"

        headers = ClientHeaders(
            username=utils.get_username(),
            state=self.status,
            task=None,
        )

        websocket = await websockets.connect(uri, headers=headers.model_dump(), timeout=3)
        ip = websocket.remote_address[0]

        return WebsocketRPCServer(self, socket.gethostbyaddr(ip)[0], ip, websocket)

    def start(self) -> None:
        self.running = True

        asyncio.run(self._start())

        self.running = False

    async def _send(self, message: RPCRequest | RPCResponse) -> None:

        if self.server is None:
            raise ValueError("server must be registerred before a message can be sent.")

        socket = self.server.socket
        await socket.send(message.model_dump_json())

    async def _start(self) -> None:
        self.server = await self.connect()

    async def _client_consumer(self, client: WebsocketRPCClient) -> None:
        async for raw_data in client.socket:
            message = self.receive(str(raw_data))

    async def _client_producer(self, client: WebsocketRPCClient) -> None:
        while True:
            if not self.send_queue.empty():
                message = self.send_queue.get(block=False)
                await client.socket.send(message.model_dump_json())

    def _parse_message(self, raw_data: str) -> Callable | Any | RPCError:

        data = json.loads(raw_data)

        kind = data["kind"]
        if kind == RPCRequest.kind:
            message = RPCClient.parse_request(data)
        elif kind == RPCRequest.kind:
            message = RPCClient.parse_response(data)
        else:
            raise ValueError(f"Unknown kind {raw_data!r}")

        return message

    def _get_message_id(self, raw_data: str) -> uuid.UUID:
        data = json.loads(raw_data)

        return data["message_id"]


def get_server() -> str: ...
