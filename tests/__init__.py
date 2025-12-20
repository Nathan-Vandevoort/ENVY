import logging

import envy
from envy import utils


def init() -> None:
    utils.init_logging()
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger(envy.__name__).setLevel(logging.DEBUG)
