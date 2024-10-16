import io

# noinspection PyUnresolvedReferences
from utils import config_bridge
# noinspection PyUnresolvedReferences
import envyRepo.prep_env  # this is important to prepare the virtual environment
import logging
import os
import sys
from envyRepo.envyLib import envy_utils as eutils
from envyRepo.envyLib import envy_logger
from datetime import datetime
import socket
import qdarkstyle
from envyRepo.envyUI.envyInstanceUI.envyMainWindow import EnvyMainWindow
from qasync import QApplication, QEventLoop
import io


class CustomFormatter(logging.Formatter):
    # Define color codes
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    # Define format
    format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'

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

log_path = os.path.join(str(config_bridge.Config.ENVYPATH), 'Logs', f'{socket.gethostname()}.log')
if not os.path.isdir(os.path.join(str(config_bridge.Config.ENVYPATH), 'Logs')):
    os.makedirs(os.path.join(str(config_bridge.Config.ENVYPATH), 'Logs'))

if not os.path.isfile(log_path):
    with open(log_path, 'w') as file:
        file.close()
today = datetime.now()
current_time = today.strftime('%H:%M:%S')

with open(log_path, 'a') as file:
    file.write(f'\n\n{today}\n{current_time}')
    file.close()

log_handler = logging.FileHandler(log_path, 'a')
log_handler.setFormatter(CustomFormatter())

stream = io.StringIO()
logger = envy_logger.get_logger(stream, html=True, level=logging.DEBUG)
logger.addHandler(log_handler)

if not os.path.isdir(os.path.join(config_bridge.Config.ENVYPATH, 'Jobs', 'Jobs')):
    eutils.make_job_directories()

app = QApplication(sys.argv)
loop = QEventLoop(app)
app.setStyleSheet(qdarkstyle.load_stylesheet_pyside6())
window = EnvyMainWindow(loop, app, logger, stream)
window.show()
loop.run_forever()
sys.exit(app.exec())
