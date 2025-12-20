import logging
import queue
import socket
import typing

import websockets
from websockets.server import WebSocketServerProtocol

from envy.lib.core.data import Client, ClientStatus, Console
from envy.lib.core.message import Message
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
        self._sockets: dict[str, WebSocketServerProtocol] = {}
        self._consoles: dict[str, Console] = {}

        # callbacks
        self.register_client_callback: typing.Callable | None = None
        self.register_console_callback: typing.Callable | None = None
        self.unregister_client_callback: typing.Callable | None = None
        self.unregister_console_callback: typing.Callable | None = None

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

    def register_client(self, ip: str, websocket: WebSocketServerProtocol, headers: websockets.Headers) -> bool:
        name = headers.get('name')
        status = headers.get('status')
        job = headers.get('job')
        task = headers.get('task')

        if None in (name, status):
            logger.error(f'Failed to register client - Invalid headers.')
            logger.debug(f'{headers=}')
            return False

        if not isinstance(name, str):
            logger.error(f'Failed to register client - Invalid name')
            logger.debug(f'{name=}')
            return False

        if job and task:
            try:
                validated_job = int(job)
                validated_task = int(task)
            except TypeError:
                logger.error(f'Failed to register client - Invalid Job or Task ID')
                logger.debug(f'{job=}, {task=}')
                return False

        try:
            status = ClientStatus(status)
        except ValueError:
            logger.error(f'{name} has an invalid status: {status}')
            return False

        new_client = Client(
            name=name,
            ip=ip,
            status=status,
            job_id=validated_job,
            task_id=validated_task,
        )

        self._clients[name] = new_client
        self._sockets[name] = websocket
        logger.info(f'Registered client: {name}')
        self._run_callback(self.register_client_callback, new_client)
        return True

    def register_console(self, console: str, ip: str, websocket: WebSocketServerProtocol) -> bool:
        new_console = Console(ip=ip, socket=websocket)
        self._consoles[console] = new_console
        logger.info(f'Registered console: {console}')
        self._run_callback(self.register_console_callback, new_console)
        return True

    async def client_consumer(self, client_name: str) -> None:
        websocket = self._sockets[client_name]
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
        del self._sockets[client_name]
        self._run_callback(self.unregister_client_callback, client_name)
        logger.debug(f'Unregistered client {client_name}.')

    def unregister_console(self, console_name: str) -> None:
        if console_name not in self._consoles:
            logger.warning(f'Cannot unregister console because console is not registered: {console_name}')
            return
        del self._consoles[console_name]
        self._run_callback(self.unregister_console_callback, console_name)
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

    def _handle_message(self, m: websockets.Data):
        message = Message.decode(str(m))
        if not message:
            return
        self._message_queue.put(message)

    @staticmethod
    def _run_callback(callback: typing.Callable | None, *args, **kwargs) -> None:
        if not callback:
            logger.debug(f'callback is not registered')
            return
        callback(*args, **kwargs)
