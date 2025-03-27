import socket
import os
import subprocess
import logging
import sys

from envy.lib.core.taskrunner import TaskRunner
from envy.lib.core.message_handler import MessageHandler
from envy.lib.core.client.websocket_client import WebsocketClient
from envy.lib.core.data import ClientState
from envy.lib.utils.logger import ANSIFormatter

logger = logging.getLogger(__name__)


class Client:
    def __init__(self):
        self.state = ClientState(name=socket.gethostname())
        self._task_runner = TaskRunner()

        # Init websocket client.
        self._websocket_client = WebsocketClient()
        self._websocket_client.client_state = self.state
        self._websocket_client.disconnection_callback = on_disconnect

        # Init message handler.
        self._message_handler = MessageHandler()
        process_queue = self._websocket_client.receive_queue()
        self._message_handler.set_process_queue(process_queue)
        self._message_handler.module = 'NV'

    def start(self) -> None:
        logger.info(f'Starting client...')
        self._task_runner.create_task(self._websocket_client.start(), 'websocket_client')
        self._task_runner.start()

    def stop(self) -> None:
        logger.info(f'Stopping client...')
        self._task_runner.stop()


def on_disconnect() -> None:
    """A callback to be run when the client disconnects from the server."""

    logger.debug(f'Running on disconnect callback...')
    my_dir = os.path.dirname(__file__)
    dir_pieces = my_dir.split(os.path.sep)
    dir_pieces.pop()
    server_dir = os.path.sep.join(dir_pieces)
    server_path = os.path.join(server_dir, 'server', 'core.py')

    # Launch with venv interpreter.
    logger.info(f'Launching server...')
    interpreter_path = sys.executable
    subprocess.Popen([interpreter_path, server_path])


if __name__ == '__main__':
    root_logger = logger.root
    root_logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(ANSIFormatter(prefix='Client'))
    root_logger.addHandler(handler)

    logging.getLogger('websockets').setLevel(logging.INFO)

    client = Client()
    client.start()
