import logging

import envy.lib.core.server.core as Server

log_format = "[%(levelname)s:%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
logging.basicConfig(level=logging.DEBUG, format=log_format)
logger = logging.getLogger(__name__)


def test_start():
    logger.debug(f'test: start server')
    server = Server.Server()
    server.start()


if __name__ == '__main__':
    test_start()
