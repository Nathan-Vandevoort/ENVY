import logging

from envy import api
import time

logger = logging.getLogger(__name__)


class ExamplePlugin(api.Plugin):
    name = 'example'

    def run(self, start: float, end: float, increment: float, *args, **kwargs) -> None:
        logger.debug("Houdini plugin started")
        print(f'{start=}, {end=}, {increment=}')

        for i in range(100):
            print(i)
            time.sleep(0.1)
