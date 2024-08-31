import config_bridge
import envyRepo.prep_env  # this is important to prepare the virtual environment
import asyncio
import logging
from envyRepo.envyCore.consoleObject import Console
import os

os.system('color')
class CustomFormatter(logging.Formatter):
    # Define color codes
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    # Define format
    format = '%(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: yellow + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

loop = asyncio.new_event_loop()
con = Console(event_loop=loop, logger=logger)
console_task = loop.create_task(con.start())
loop.run_forever()
