import envy
import asyncio
import json
import logging
import os
import queue
import socket
import sys

import websockets

import envy.lib.network.message as m
from envy.lib.jobs import scheduler
from envy.lib.jobs.enums import Status
from envy.lib.network.messagepurpose import MessagePurpose
from envy.lib.utils import utils as eutils
from envy.lib.utils import config
from envy.lib.core import taskrunner

SRV = sys.modules.get('Server_Functions')


def update_clients_file(dir, clients: dict):
    clients_file = os.path.join(dir, 'clients.json')
    clients = {k: {k2: v2 for k2, v2 in v.items() if k2 != 'Socket'} for k, v in clients.items()}
    with open(clients_file, 'w') as cf:
        json.dump(clients, cf)


logger = logging.getLogger(__name__)


class Server:

    def __init__(self):
        self.hostname = socket.gethostname()
        self.my_ip = socket.gethostbyname(self.hostname)
        self.server_file = None

        configs = config.Config()
        self.port = configs.DISCOVERYPORT
        self.server = None

        self.clients = {}
        self.consoles = {}
        self.hash = eutils.get_hash()
        self.receive_queue = queue.Queue()

        self.task_runner = taskrunner.TaskRunner()

        # -------------------- directories ------------------------------------
        self.server_directory = os.path.join(envy.__file__, 'Connections')

        # -------------------- Job --------------------------------------
        # self.job_scheduler = scheduler.Scheduler()

    def get_input_queue(self):
        return self.receive_queue

    async def check_passkey(self, path, request_headers):
        passkey = request_headers.get('Passkey')
        name = request_headers.get('Name')
        logger.debug(f'received connection from {name} with purpose {path}')

        if path == '/client':
            if name in self.clients:
                logger.debug(f'rejecting client connection,Reason: client already exists {name}')
                return 500, [("Content-Type", "text/plain")], b"connection from client already exists"

        if path == '/console':
            if name in self.consoles:
                logger.debug(f'rejecting console connection,Reason: console already exists {name}')
                return 500, [("Content-Type", "text/plain")], b"connection from client already exists"

        if passkey != self.hash:
            logger.debug("Invalid Passkey, rejecting connection")
            return 403, [("Content-Type", "text/plain")], b"Invalid passkey"

        logger.debug(f"validated connection from {name}")
        return None

    async def handler(self, websocket):
        client_ip = websocket.remote_address[0]
        request_headers = websocket.request_headers

        if websocket.path == '/client':
            client = request_headers['Name']
            # Register new client
            await self.register_client(client, client_ip, websocket)

            # Send the client name of server
            await SRV.send_attribute_to_client(self, client, 'hostname', 'server_name')

            # Start tasks per connection
            consumer_task = asyncio.create_task(self.client_handler(websocket, client))
            done, pending = await asyncio.wait(
                [consumer_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()

            await self.unregister_client(client)

        if websocket.path == '/console':
            console = request_headers['Name']
            await self.register_console(console, client_ip, websocket)

            # Start tasks per connection
            consumer_task = asyncio.create_task(self.console_handler(websocket, console))
            done, pending = await asyncio.wait(
                [consumer_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()

            self.unregister_console(console)

        if websocket.path == '/health_check':
            await websocket.recv()
            await websocket.send('pong')

    # handles incoming messages from console
    async def console_handler(self, websocket, console):
        try:
            async for message in websocket:
                try:
                    deserialized_message = json.loads(message)
                    message_object = m.build_from_message_dict(deserialized_message)
                    logger.info(f"Console {console} sent message: ({message_object})")
                    status = await self.console_consumer(message_object)
                    if not status:
                        logger.warning(f'unknown message received ({message_object}) -> {message_object.as_dict()}')
                        continue
                except json.JSONDecodeError as e:
                    logger.error(f'Failed to decode message: {e}')
                except Exception as e:
                    logger.error(f'Unexpected error while processing message: {e}')
        except (
            websockets.exceptions.ConnectionClosedError,
            websockets.ConnectionClosed,
            websockets.ConnectionClosedOK,
        ):
            logger.debug(f'connection closed with {console}')
            return 0  # connection was closed

    # handles incoming messages clients
    async def client_handler(self, websocket, client):
        client_ip = websocket.remote_address[0]
        try:
            async for message in websocket:
                deserialized_message = json.loads(message)
                message_object = m.build_from_message_dict(deserialized_message)
                logger.debug(f"Client {client} sent message: ({message_object})")
                status = await self.client_consumer(message_object)  # will return True or False if the message was acted upon
                if not status:
                    logger.warning(f'unknown message received ({message_object}) -> {message_object.as_dict()}')
                    continue
        except (
            websockets.exceptions.ConnectionClosedError,
            websockets.ConnectionClosed,
            websockets.ConnectionClosedOK,
        ):
            logger.debug(f'connection closed with {client}')
            return 0  # connection was closed

    # do from incoming connection
    async def client_consumer(self, message: m.Message | m.FunctionMessage):
        purpose = message.get_type()

        if purpose == MessagePurpose.FUNCTION_MESSAGE:
            if not isinstance(message, m.FunctionMessage):
                logger.error(f"Message ({message}) is not a FunctionMessage")
                return False

            success = await self.execute(message)
            return success

        # if request is never executed
        return False

    async def execute(self, message: m.FunctionMessage) -> bool:
        logger.debug(f'executing {message}')
        function = message.as_function()
        try:
            await self.async_exec('await SRV.' + function)
        except Exception as e:
            logger.error(f'Failed while executing: {function} -> {e}')
            error_message = m.Message('server_error_message')
            error_message.set_type(MessagePurpose.MEDIUM_SERVER_ERROR)
            error_message.set_message(f'Failed while executing {function}, {e}')
            await SRV.send_to_consoles(self, error_message)
            return False
        return True

    async def pass_on(self, message: m.Message):
        try:
            logger.debug(f'pass_on: ({message})')
            function_message = m.build_from_message_dict(message.get_data(), logger=logger)
            classifier = message.get_message()
            send_targets = eutils.get_applicable_clients(classifier, list(self.clients))
            await SRV.send_to_clients(self, send_targets, function_message)
            return True
        except Exception:
            return False

    async def console_consumer(self, message: m.Message | m.FunctionMessage):
        logger.debug(f'received message from console: {message}')
        purpose = message.get_type()

        if purpose == MessagePurpose.FUNCTION_MESSAGE:
            if not isinstance(message, m.FunctionMessage):
                logger.error(f"Message ({message}) is not a FunctionMessage")
                return False

            success = await self.execute(message)
            return success

        if purpose == MessagePurpose.PASS_ON:
            success = await self.pass_on(message)
            return success

    async def register_client(self, client, ip, websocket):
        logger.info(f"Registering client: {client}")

        new_client_data = {
            'IP': ip,
            'Socket': websocket,
            'Status': Status.WORKING,
            'Job': None,
            'Allocation': None,
        }
        self.clients[client] = new_client_data
        update_clients_file(self.server_directory, self.clients)

        json_safe_client_data = {
            'IP': ip,
            'Status': Status.IDLE,
            'Job': None,
            'Allocation': None,
        }

        await SRV.console_register_client(self, client, json_safe_client_data)

    async def register_console(self, console, ip, websocket):
        logger.debug(f'Registering console: {console}')
        self.consoles[console] = {'IP': ip, 'Socket': websocket}
        await SRV.send_clients_to_console(self)

    async def unregister_client(self, client):
        logger.info(f'Unregistering Client: {client}')
        del self.clients[client]
        update_clients_file(self.server_directory, self.clients)
        await SRV.console_unregister_client(self, client)

    def unregister_console(self, console):
        logger.info(f'Unregistering Console: {console}')
        del self.consoles[console]

    def write_server_file(self):
        logger.debug('writing server file')

        try:
            os.rename(
                os.path.join(self.server_directory, 'server.txt'), os.path.join(self.server_directory, 'server.txt')
            )  # rename file to same name to check if its being used by another server
        except OSError:
            raise PermissionError('File is being used by another server')

        self.server_file = open(os.path.join(self.server_directory, 'server.txt'), 'w')
        self.server_file.write(self.my_ip)
        self.server_file.flush()

    async def start_server(self):
        # TODO: make the server write to the server file or however I want to lock that
        logger.debug(f'starting websocket server')

        self.server = await websockets.serve(
            self.handler,
            self.my_ip,
            self.port,
            process_request=self.check_passkey,
        )

        logger.debug(f'Created job scheduler task')

        await self.server.wait_closed()

    def start(self):
        logger.debug('starting server')
        self.task_runner.create_task(self.start_server(), 'websocket_server')
        self.task_runner.start()

    def start_job_scheduler(self):
        raise NotImplemented()
        # TODO: implement this
        # self.job_scheduler = scheduler.Scheduler()

    async def async_exec(self, s: str) -> None:
        """
        this one is a copy of the one in envy_utils but I put it here so it has access to the prepared environment
        an Async version of exec that I found on stack overflow and tbh idk how it works
        Update: I think I do know how it works kinda.
        -Nathan

        :param s: input string
        :return: None
        """
        import ast

        logger.debug(f'executing: {s}')
        code = compile(
            s,
            '<string>',
            'exec',
            flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
        )
        coroutine = eval(code)
        if coroutine is not None:
            await coroutine


if __name__ == '__main__':
    server = Server()
    server.start()
