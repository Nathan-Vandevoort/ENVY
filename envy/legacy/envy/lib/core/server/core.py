from __future__ import annotations

import asyncio
import logging
import os
import sys

import envy
from envy.lib.core import taskrunner
from envy.lib.core.server.server_message_handler import ServerMessageHandler
from envy.lib.core.server.websocket_server import WebsocketServer
from envy.lib.db import db
from envy.lib.core.data import Client, Console
from envy.lib.core.message import Message, MessageTarget, MessageType
from envy.lib.utils.logger import ANSIFormatter

LOCK_INTERVAL = 5

logger = logging.getLogger(__name__)


class Server:
    def __init__(self):

        # Init task runner.
        self.task_runner = taskrunner.TaskRunner()
        self.task_runner.suppress_error(OSError)
        self.task_runner.stop_loop_on_task_failure = True

        # Init websocket server.
        self.websocket_server = WebsocketServer()
        self.websocket_server.register_client_callback = self.register_client
        self.websocket_server.unregister_client_callback = self.unregister_client
        self.websocket_server.register_console_callback = self.sync_clients

        # Init message handler.
        self.message_handler = ServerMessageHandler(self, 'envy.Plugins.Server_Functions')
        self.process_queue = self.websocket_server.get_output_queue()
        self.message_handler.set_process_queue(self.process_queue)

        # Init database.
        self._init_database()

        # Init values.
        self.clients = self.websocket_server.clients()
        self.consoles = self.websocket_server.consoles()

    def _init_database(self):
        path = os.path.join(os.path.dirname(envy.__file__), 'Jobs')
        database = 'Envy_Database.db'

        if not os.path.isdir(path):
            os.makedirs(path)

        self._database = db.DB(os.path.join(path, database))
        self._database.start()

    def acquire_lock(self) -> bool:
        ip = self.websocket_server.ip
        try:
            self._database.acquire_lock(ip)
        except IOError:
            return False

        logger.info('Acquired database lock')
        self.task_runner.create_task(self.maintain_lock(), 'maintain_lock')
        return True

    def start(self):
        logger.info(f'Starting server')
        if not self.acquire_lock():
            logger.debug('Failed to acquire database lock.')
            logger.error('Server already exists.')
            self.stop()
            return
        self.task_runner.create_task(self.websocket_server.start(), 'websocket_server')
        self.task_runner.create_task(self.message_handler.start(), 'message_handler')
        self.task_runner.start()

    def stop(self):
        logger.info(f'Stopping server...')
        if self.task_runner.running:
            self.task_runner.stop()
        logger.info(f'Server stopped.')
        sys.exit(0)

    async def maintain_lock(self) -> None:
        ip = self.websocket_server.ip
        while True:
            self._database.maintain_lock(ip)
            await asyncio.sleep(LOCK_INTERVAL)

    def sync_clients(self, console: Console) -> None:
        # Send all the clients to all consoles.
        logger.debug(f'Syncing clients with consoles')
        client_datas = []
        for client in self.clients:
            # Make a copy of the client data and take out the socket because a websocket
            # is not json serializable.
            client_data = self.clients[client]
            client_datas.append(client_data)

        new_message = Message(
            message_type=MessageType.FUNCTION_MESSAGE,
            message_target=MessageTarget.CONSOLE,
            function='register_clients',
            kwargs={'clients': client_datas},
        )
        self.process_queue.put(new_message)

    def register_client(self, client: Client) -> None:
        # Send a message to the console with the new client data.
        logger.debug(f'Running register client callback...')
        new_message = Message(
            message_type=MessageType.FUNCTION_MESSAGE,
            message_target=MessageTarget.CONSOLE,
            function='register_clients',
            kwargs={'clients': (client.to_dict(encode_json=True),)},
        )
        self.process_queue.put(new_message)

    def unregister_client(self, client_name: str) -> None:
        # Send a message to the client with the client name.
        logger.debug(f'Running unregister client callback...')
        new_message = Message(
            message_type=MessageType.FUNCTION_MESSAGE,
            message_target=MessageTarget.CONSOLE,
            function='unregister_clients',
            kwargs={'clients': (client_name,)},
        )
        self.process_queue.put(new_message)


def main() -> None:
    root_logger = logger.root
    root_logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(ANSIFormatter(prefix=f'Server {os.getpid()}'))
    root_logger.addHandler(handler)
    logging.getLogger('websockets').setLevel(logging.INFO)

    server = Server()
    server.start()


if __name__ == '__main__':
    main()
