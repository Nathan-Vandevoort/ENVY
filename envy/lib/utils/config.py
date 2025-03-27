import envy
import configparser
import os
import logging

logger = logging.getLogger(__name__)

config_path = os.path.join(envy.__file__, os.path.pardir)
logger.debug(f'Config path: {config_path}')

config = configparser.ConfigParser()
config.read(os.path.join(config_path, 'config.ini'))


class Config:
    DISCOVERYPORT = config.getint('DEFAULT', 'discoveryport')
    HOUDINIBINPATH = config.get('DEFAULT', 'houdinibinpath').replace('\\', '/')
    MAYABINPATH = config.get('DEFAULT', 'mayabinpath').replace('\\', '/')
    TEMP = config.get('DEFAULT', 'TEMP')
