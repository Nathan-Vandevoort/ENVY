from __future__ import annotations

import asyncio
import logging
import os
import sys

import websockets.exceptions

import envy
from envy.Plugins import Server_Functions as SRV
from envy.lib.core import taskrunner
from envy.lib.core.message_handler import MessageHandler
from envy.lib.core.server.websocket_server import WebsocketServer
from envy.lib.db import db
from envy.lib.network import message
from envy.lib.utils.logger import ANSIFormatter
from envy.lib.utils.utils import get_applicable_clients

LOCK_INTERVAL = 5

logger = logging.getLogger(__name__)


class ServerMessageHandler(MessageHandler):

    def __init__(self, srv: Server):
        super().__init__()
        self.server = srv

    async def _handle_message(self, m: message.Message | message.FunctionMessage) -> None:
        if m.get_type() == message.MessageType.FUNCTION_MESSAGE:
            await self._execute_function_message(m)

        elif m.get_type() == message.MessageType.PASS_ON:
            try:
                await self._pass_on(m)
            except RuntimeError:
                logger.debug(f'Failed to pass on message {m}')

    async def _pass_on(self, m: message.Message):
        logger.debug(f'Passing on message: ({m})')
        function_message = message.build_from_message_dict(m.get_data())
        classifier = m.get_message()
        send_targets = get_applicable_clients(classifier, list(self.server.clients))
        await SRV.send_to_clients(self, send_targets, function_message)


class Server:
    def __init__(self):

        # Init task runner.
        self.task_runner = taskrunner.TaskRunner()
        self.task_runner.stop_loop_on_task_failure = True
        self.task_runner.suppress_error(OSError)

        # Init websocket server.
        self.websocket_server = WebsocketServer()

        # Init message handler.
        self.message_handler = ServerMessageHandler(self)
        process_queue = self.websocket_server.get_output_queue()
        self.message_handler.set_process_queue(process_queue)
        self.message_handler.module = 'SRV'

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

    async def maintain_lock(self):
        ip = self.websocket_server.ip
        while True:
            self._database.maintain_lock(ip)
            await asyncio.sleep(LOCK_INTERVAL)


