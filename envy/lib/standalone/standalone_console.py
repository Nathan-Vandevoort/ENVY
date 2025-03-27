import asyncio
import logging

from envy.lib.core.console.core import Console
from envy.lib.core.taskrunner import TaskRunner

logger = logging.getLogger(__name__)


class StandaloneConsole:

    def __init__(self) -> None:

        # Init console core.
        self.console = Console()

        # Init task runner.
        self.task_runner = TaskRunner()

    def start(self) -> None:
        self.task_runner.create_task(self.console.start(), 'Console Core')
        logger.debug(f'running')
        self.task_runner.start()


if __name__ == '__main__':
    handler = logging.StreamHandler()
    prefix = "[Standalone Console]"
    formatter = f'{prefix} %(asctime)s - %(name)s.%(funcName)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=formatter)
    logging.getLogger('websockets').setLevel(logging.WARNING)

    console = StandaloneConsole()
    console.start()
