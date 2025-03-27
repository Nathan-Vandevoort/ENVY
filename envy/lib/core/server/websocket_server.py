import asyncio
import json
import logging
import queue
import socket
import typing
from json import JSONDecodeError

import websockets
from websockets.server import WebSocketServerProtocol

from envy.lib.core.data import Client, ClientStatus, Console
from envy.lib.network import message as envy_message
from envy.lib.utils.utils import get_hash

logger = logging.getLogger(__name__)


# TODO: make this read from config
PORT = 3720


class WebsocketServer:

    def __init__(self):
        self.ip = socket.gethostbyname(socket.gethostname())
        self.server: typing.Awaitable[websockets.WebSocketServer] | None = None
        self._key = get_hash()
        self._message_queue = queue.Queue()
        self._clients: dict[str, Client] = {}
        self._consoles: dict[str, Console] = {}

    def get_output_queue(self):
        return self._message_queue

    def clients(self) -> dict[str, Client]:
        return self._clients

    def consoles(self) -> dict[str, Console]:
        return self._consoles

    async def validate_connection(self, path: str, headers: typing.Mapping[str, str]) -> tuple[int, list[tuple[str, str]], bytes] | None:
        key = headers.get('passkey', None)
        name = headers.get('name', None)

        if not key or not name:
            logger.debug(f'Rejected: invalid headers')
            return 415, [('Content-Type', 'text/plain')], b'Invalid Headers'

        if key != self._key:
            logger.debug(f'Rejected: invalid key')
            return 415, [('Content-Type', 'text/plain')], b'Invalid Key'

        if path == '/client':
            if name in self._clients:
                logger.debug(f'Rejecting client {name} because client is already connected')
                return 500, [("Content-Type", "text/plain")], b"connection from client already exists"

        if path == '/console':
            if name in self._consoles:
                logger.debug(f'Rejecting console {name} because console is already connected.')
                return 500, [("Content-Type", "text/plain")], b"connection from console already exists"

        logger.info(f'Validated connection: {name}')
        return None

    async def handler(self, websocket: WebSocketServerProtocol) -> None:

        connection_ip = websocket.remote_address[0]
        headers = websocket.request_headers
        connection_name = headers.get('name', None)

        if not connection_name:
            logger.error('New connection did not have a "name" in its header. Refusing connection')
            return

        logger.debug(f'Handling connection from: {connection_name}')

        if websocket.path == '/client':
            if not self.register_client(connection_ip, websocket, headers):
                return
            await self.client_consumer(connection_name)
            self.unregister_client(connection_name)

        if websocket.path == '/console':
            if not self.register_console(connection_name, connection_ip, websocket):
                return
            await self.console_consumer(connection_name)
            self.unregister_console(connection_name)

    def register_client(self, ip: str, websocket: WebSocketServerProtocol, headers: dict) -> bool:
        try:
            name = headers.get('name')
            status = headers.get('status')
            job = headers.get('job')
            task = headers.get('task')
        except ValueError as e:
            logger.error(f'Failed to register client: {e}')
            logger.debug(f'Headers were: {headers}')
            return False

        try:
            status = ClientStatus(status)
        except ValueError as e:
            logger.error(f'{name} has an invalid status: {status}')
            raise ValueError from e

        new_client = Client(
            ip=ip,
            socket=websocket,
            status=status,
            job=job,
            task=task,
        )

        self._clients[name] = new_client
        logger.info(f'Registered client: {name}')
        return True

    def register_console(self, console: str, ip: str, websocket: WebSocketServerProtocol) -> bool:
        self._consoles[console] = Console(ip=ip, socket=websocket)
        logger.info(f'Registered console: {console}')
        # TODO: Should the server write clients to the database?
        # await SRV.send_clients_to_console(self)
        return True

    async def client_consumer(self, client_name: str) -> None:
        websocket = self._clients[client_name].socket
        try:
            async for message in websocket:
                logger.debug(f'{client_name}: {message}')
                self._handle_message(message)
        except websockets.ConnectionClosedOK:
            logger.debug(f'{client_name}: Connection closed')
        except websockets.ConnectionClosedError as e:
            logger.warning(f'{client_name}: Connection closed with error ({e})')

    async def console_consumer(self, console_name: str) -> None:
        websocket = self._consoles[console_name].socket
        try:
            async for message in websocket:
                logger.debug(f'{console_name}: {message}')
                self._handle_message(message)
        except websockets.ConnectionClosedOK:
            logger.debug(f'{console_name}: Connection closed')
        except websockets.ConnectionClosedError as e:
            logger.warning(f'{console_name}: Connection closed with error ({e})')

    def unregister_client(self, client_name: str) -> None:
        if client_name not in self._clients:
            logger.warning(f'Cannot unregister client because client is not registered: {client_name}')
            return
        del self._clients[client_name]
        logger.debug(f'Unregistered client {client_name}.')

    def unregister_console(self, console_name: str) -> None:
        if console_name not in self._consoles:
            logger.warning(f'Cannot unregister console because console is not registered: {console_name}')
            return
        del self._consoles[console_name]
        logger.debug(f'Unregistered console {console_name}.')

    async def start(self):
        logger.debug(f'Started')
        server = await websockets.serve(
            self.handler,
            self.ip,
            PORT,
            process_request=self.validate_connection,
        )

        await server.wait_closed()

    def stop(self):
        raise InterruptedError('stop signal received')

    def _handle_message(self, message: str):
        try:
            message_as_dict = json.loads(message)
        except JSONDecodeError as e:
            logger.warning(f'Failed to decode message: {e}')
            return

        try:
            message_object = envy_message.build_from_message_dict(message_as_dict)
        except ValueError as e:
            logger.warning(f'Failed to build Message: {e}')
            return

        self._message_queue.put(message_object)
