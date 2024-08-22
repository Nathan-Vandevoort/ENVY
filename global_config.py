 #!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
global_config.py: intended to access the users config file as well as provide easy access to global variables
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"
import sys

class Config():
    DISCOVERYPORT = 37020
    #ENVYPATH = 'Z:/school/ENVY/__ENVYTEST__/'
    ENVYPATH = 'Z:/Envy_21/__ENVYTEST__/'
    TIMEOUT = 5


sys.path.append(Config.ENVYPATH)