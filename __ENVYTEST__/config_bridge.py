#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
config_bridge.py: makes the variables set in the config.ini file available in a pythonic way
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"

import sys
import os
import configparser

abs_file = os.path.abspath(__file__)
file_dir = os.path.dirname(abs_file)

config = configparser.ConfigParser()
config.read(os.path.join(file_dir, 'config.ini'))

class Config:
    DISCOVERYPORT = config.getint('DEFAULT', 'discoveryport')
    ENVYPATH = config.get('DEFAULT', 'envypath')
    REPOPATH = config.get('DEFAULT', 'repopath')
    HOUDINIBINPATH = config.get('DEFAULT', 'houdinibinpath')
    TEMP = config.get('DEFAULT', 'TEMP')


# -------------------------------------------------------------- THE LINES BELOW ARE IMPORTANT -------------------------------------------------------------------
sys.path.append(os.path.join(Config.ENVYPATH, 'Plugins'))
sys.path.append(Config.REPOPATH)
import prep_env

if __name__ == '__main__':
    value = input('Reset config press enter to confirm or close out of the console if not')
    default_data = {
        'DISCOVERYPORT': 37020,
        'ENVYPATH': 'Z:/ENVY/',
        'REPOPATH': '//titansrv/studentShare/__ENVY__/ENVY_Repo/',
        'HOUDINIBINPATH': 'C:/Program Files/Side Effects Software/Houdini 20.0.653/bin/',
        'TEMP': 'C:/Temp/'
    }
    with open('config.ini', 'w') as config_file:
        config = configparser.ConfigParser()
        config['DEFAULT'] = default_data
        config.write(config_file)
    input('Config file has been reset press enter to close console')