# noinspection PyUnresolvedReferences
# noinspection PyUnresolvedReferences
import envy.lib.prep_env  # this is important to prepare the virtual environment
import logging
import os
import sys
from envy.lib.utils import utils as eutils, logger, config
from datetime import datetime
import socket
import qdarkstyle
from envy.lib.gui.envyInstanceUI.envyMainWindow import EnvyMainWindow
from qasync import QApplication, QEventLoop
import io

log_path = os.path.join(str(config.Config.ENVYPATH), 'Logs', f'{socket.gethostname()}.log')
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

stream = io.StringIO()
logger = envy_logger.get_logger(stream, html=True, level=logging.INFO)
logger.addHandler(log_handler)

if not os.path.isdir(os.path.join(config.Config.ENVYPATH, 'Jobs', 'Jobs')):
    eutils.make_job_directories()

app = QApplication(sys.argv)
loop = QEventLoop(app)
app.setStyleSheet(qdarkstyle.load_stylesheet_pyside6())
window = EnvyMainWindow(loop, app, logger, stream)
window.show()
loop.run_forever()
sys.exit(app.exec())
