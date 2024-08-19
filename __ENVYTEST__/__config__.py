#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
global_config.py: intended to access the users config file as well as provide easy access to global variables
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"

import sys
import os

class Config:
    DISCOVERYPORT = 37020
    ENVYPATH = 'Z:/school/ENVY/__ENVYTEST__/'
    TIMEOUT = 5
    REPOPATH = 'Z:/school/ENVY/'
    HOUDINIBINPATH = 'C:/Program Files/Side Effects Software/Houdini 20.0.653/bin/'

# -------------------------------------------------------------- THE LINES BELOW ARE IMPORTANT -------------------------------------------------------------------

sys.path.append(os.path.join(Config.ENVYPATH, 'Plugins'))
sys.path.append(Config.REPOPATH)
