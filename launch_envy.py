import prep_env  # this is important to prepare the virtual environment
import asyncio
import logging
import os
from envyLib import envy_utils as eutils
from config import Config
from envyCore.envy import Envy
from datetime import datetime
import socket
import sys


formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)

log_path = os.path.join(str(Config.ENVYPATH), 'Logs', f'{socket.gethostname()}.log')
if not os.path.isdir(os.path.join(str(Config.ENVYPATH), 'Logs')):
    os.makedirs(os.path.join(str(Config.ENVYPATH), 'Logs'))

if not os.path.isfile(log_path):
    with open(log_path, 'w') as file:
        file.close()
today = datetime.now()
current_time = today.strftime('%H:%M:%S')

with open(log_path, 'a') as file:
    file.write(f'\n\n{today}\n{current_time}')
    file.close()

log_handler = logging.FileHandler(log_path, 'a')
log_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

if not os.path.isdir(os.path.join(Config.ENVYPATH, 'Jobs', 'Jobs')):
    eutils.make_job_directories()

loop = asyncio.new_event_loop()
envy = Envy(loop, logger=logger)
envy_task = loop.create_task(envy.run())
loop.run_forever()
