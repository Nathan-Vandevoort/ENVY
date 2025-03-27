import json
import typing

import websockets
import asyncio
import socket

import logging

from envy.lib.core.taskrunner import TaskRunner
from envy.lib.network.types import ConnectionType
from envy.lib.network.message import Message, build_from_message_dict, MessageTarget
from envy.lib.utils.utils import get_hash
from envy.lib.db.utils import get_server_ip
from envy.lib.core.data import ClientState

PORT = 3720
TIMEOUT = 5

logger = logging.getLogger(__name__)


class WebsocketClient:

    def __init__(self):
        self.websocket: websockets.WebSocketClientProtocol | None = None
        self.client_state = ClientState(name=socket.gethostname())
        self._send_queue = asyncio.Queue()
        self._receive_queue = asyncio.Queue()
        self.disconnection_callback: typing.Callable | None = None

        # Init task runner.
        self.task_runner = TaskRunner()
        self.task_runner.suppress_error(websockets.exceptions.ConnectionClosedError)

    def send_queue(self) -> asyncio.Queue:
        return self._send_queue

    def receive_queue(self) -> asyncio.Queue:
        return self._receive_queue

    async def start(self) -> None:
        while True:
            if self.disconnection_callback:
                self.disconnection_callback()
            server_ip = get_server_ip()
            try:
                await self.connect(server_ip)
            except (ConnectionRefusedError, TimeoutError, websockets.InvalidStatusCode) as e:
                logger.debug(f'Failed to connect: {e}')
                continue

            while self.websocket.open:
                await asyncio.sleep(0.5)

            logger.error(f'Lost connection with server.')
            self.task_runner.stop()
            self.task_runner.create_task(self.consumer(), 'Consumer')
            self.task_runner.start()

    def send_message(self, m: Message) -> None:
        logger.info(f'Adding message ({m.name}) to queue')
        logger.debug(f'Message: {m.as_dict()}')
        self._send_queue.put(m)

    async def connect(self, server_ip: str) -> None:
        """
        Connects to the provided server_ip.

        :raises websockets.InvalidURI: If the connection failed.
        :raises websockets.InvalidHandshake: If the connection failed.
        :raises asyncio.TimeoutError: If the connection timed out.
        """
        # TODO: update exceptions
        uri = f"ws://{server_ip}:{PORT}/{ConnectionType.CLIENT}"
        logger.info(f'Connecting to {server_ip}')

        headers = {
            'passkey': get_hash(),
            'name': self.client_state.name,
            'status': self.client_state.status.value,
            'job': self.client_state.job_id,
            'task': self.client_state.task_id,
        }

        websocket = await websockets.connect(uri, extra_headers=headers, timeout=TIMEOUT)
        self.websocket = websocket

    async def disconnect(self) -> None:
        """
        Closes the connection to the server.
        """

        logger.info('Disconnecting from server')
        if not self.websocket:
            logger.debug(f'Connection does not exist')
            return

        await self.websocket.close()
        self.websocket = None
        logger.info('Connection closed')

    async def consumer(self) -> None:
        """
        This function takes messages from the websocket, processes them,
        then puts them in the receive queue.
        This function is ran as an async task.
        This is a long-running function.
        """

        async for m in self.websocket:
            try:
                json.loads(m)
            except json.JSONDecodeError as e:
                logger.warning(f'Failed to parse message {e}')
                continue
            except TypeError as e:
                logger.error(f'{e}')
                continue

            try:
                message_object = build_from_message_dict(m)
            except ValueError:
                logger.error(f'Skipping invalid message.')
                logger.debug(f'message = {m}')
                continue

            if message_object.get_target() != MessageTarget.CLIENT:
                logger.error(f'Non-client message detected.')
                logger.debug(f'message = {message_object.as_dict()}')
                continue

            await self._receive_queue.put(message_object)
            logger.debug(f'Processed message {message_object!r}')
