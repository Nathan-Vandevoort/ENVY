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
file_dir = os.path.join(os.path.dirname(abs_file), os.path.pardir)

config = configparser.ConfigParser()
config.read(os.path.join(file_dir, 'config.ini'))


class Config:
    DISCOVERYPORT = config.getint('DEFAULT', 'discoveryport')
    ENVYPATH = config.get('DEFAULT', 'envypath').replace('\\', '/')
    REPOPATH = config.get('DEFAULT', 'repopath').replace('\\', '/')
    HOUDINIBINPATH = config.get('DEFAULT', 'houdinibinpath').replace('\\', '/')
    MAYABINPATH = config.get('DEFAULT', 'mayabinpath').replace('\\', '/')
    TEMP = config.get('DEFAULT', 'TEMP')


# -------------------------------------------------------------- THE LINES BELOW ARE IMPORTANT -------------------------------------------------------------------
plugin_path = os.path.join(Config.ENVYPATH, 'Plugins')
if plugin_path not in sys.path:
    print(f'Loaded Plugin_Path: {plugin_path}')
    sys.path.append(os.path.join(Config.ENVYPATH, 'Plugins'))

if Config.REPOPATH not in sys.path:
    print(f'Loaded RepoPath: {Config.REPOPATH}')
    sys.path.insert(0, Config.REPOPATH)