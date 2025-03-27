import logging
from envy.lib.core.console.websocket_console import WebsocketConsole
from envy.lib.core.message_handler import MessageHandler
from envy.lib.core.taskrunner import TaskRunner
from envy.lib.network.message import Message

logger = logging.getLogger(__name__)


class Console:
    def __init__(self) -> None:

        # Init websocket console.
        self.websocket_console = WebsocketConsole()
        self.send_queue = self.websocket_console.send_queue()
        self.receive_queue = self.websocket_console.receive_queue()

        # Init task runner.
        self.task_runner = TaskRunner()

        # Init message handler.
        self.message_handler = MessageHandler()
        self.message_handler.set_process_queue(self.receive_queue)
        self.message_handler.module = 'CONSOLE'

    async def start(self):
        logger.info(f'Starting console...')
        self.task_runner.create_task(self.websocket_console.start(), 'websocket console')
        self.task_runner.create_task(self.message_handler.start(), 'message handler')
        self.task_runner.start()

    def send_message(self, m: Message) -> None:
        if not issubclass(type(m), Message):
            logger.error(f'Invalid message.')
            logger.debug(f'{m!r}')
            return None
        self.send_queue.put(m)
