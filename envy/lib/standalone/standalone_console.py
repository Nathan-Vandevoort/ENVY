import sys
import asyncio
import logging

from envy.lib.core.console.core import Console
from envy.lib.utils.logger import ANSIFormatter

logger = logging.getLogger(__name__)


class StandaloneConsole(Console):

    def start(self) -> None:
        self.task_runner.create_task(self.gather_input(), 'Gather Input')
        super().start()

    async def gather_input(self):
        logger.debug(f'Gathering input...')
        while True:
            user_input = await self.input(f'User Input: ')
            user_input = user_input.strip()

            if not self.connected:
                logger.warning('Console is not connected to Envy network.')
            self.run(user_input)

    @staticmethod
    async def input(input_string: str) -> str:
        """Acts as an async version if the input() function"""
        await asyncio.to_thread(write_and_flush, input_string)
        return await asyncio.to_thread(sys.stdin.readline)


def write_and_flush(s: str) -> None:
    """Writes a string to the stdout and then flushes the buffer."""
    sys.stdout.write(f'{s}')
    sys.stdout.flush()
    return None


def main() -> None:
    root_logger = logger.root
    root_logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(ANSIFormatter(prefix='Console'))
    root_logger.addHandler(handler)
    logging.getLogger('websockets').setLevel(logging.WARNING)

    console = StandaloneConsole()
    console.start()


if __name__ == '__main__':
    main()
