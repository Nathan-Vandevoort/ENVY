import asyncio
import json
import logging
import queue
import typing

import websockets

from envy.lib.core.taskrunner import TaskRunner
from envy.lib.db.utils import get_server_ip
from envy.lib.core.message import Message, MessageTarget
from envy.lib.network.types import ConnectionType
from envy.lib.utils.utils import get_hash

PORT = 3720
TIMEOUT = 5

logger = logging.getLogger(__name__)


class WebsocketClient:

    def __init__(self, state_callback: typing.Callable):
        self.websocket: websockets.WebSocketClientProtocol | None = None
        self._send_queue = queue.Queue()
        self._receive_queue = queue.Queue()
        self.disconnection_callback: typing.Callable | None = None

        # Init task runner.
        self.task_runner = TaskRunner()
        self.task_runner.suppress_error(websockets.exceptions.ConnectionClosedError)

        # State
        self.connected = False
        self.state_callback = state_callback

    def send_queue(self) -> queue.Queue:
        return self._send_queue

    def receive_queue(self) -> queue.Queue:
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

            logger.info('Connected!')
            self.connected = True
            logger.debug(f'{server_ip=}')

            if self.websocket:
                self.task_runner.create_task(self.consumer(self.websocket), 'Consumer')
                self.task_runner.start()
                while self.websocket.open:
                    await asyncio.sleep(0.5)
            else:
                logger.error('Websocket connected without returning a websocket object.')
                logger.error('This state should not be reachable')

            self.connected = False
            logger.error(f'Lost connection with server.')
            self.task_runner.stop()

    def send_message(self, m: Message) -> None:
        logger.info(f'Adding message ({m.function}) to queue')
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
        state = self.state_callback()

        headers = {
            'passkey': get_hash(),
            'name': state.name,
            'status': state.status.value,
            'job': state.job_id,
            'task': state.task_id,
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

    async def consumer(self, websocket: websockets.WebSocketClientProtocol) -> None:
        """
        This function takes messages from the websocket, processes them,
        then puts them in the receive queue.
        This function is ran as an async task.
        This is a long-running function.
        """

        async for m in websocket:
            message = Message.decode(str(m))
            if not message:
                continue

            if message.message_target != MessageTarget.CLIENT:
                logger.error(f'Non-client message detected.')
                logger.debug(f'{message=!r}')
                continue

            self._receive_queue.put(message)
            logger.debug(f'Processed message {message!r}')
