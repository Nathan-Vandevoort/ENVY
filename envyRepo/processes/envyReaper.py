#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
envyReaper.py: The process responsible for signing out envy at a specified time
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"


import sys
import datetime
import time
from envyUtils.core import signOut

POLLINGRATE = 30

_, _, arguments, inTime = sys.argv

inTime = inTime.replace('"', '')
pollingrate = POLLINGRATE
arguments = arguments.replace('[', '').replace(']', '').split(',')
hours = int(inTime.split(':')[0])
minutes = int(inTime.split(':')[1])


def start():
    # get current datetime
    currentDateTime = datetime.datetime.today()
    signOutTime = currentDateTime

    # check if its been launched in the am
    if currentDateTime.hour > 7:
        signOutTime = signOutTime + datetime.timedelta(days=1)

    # replace hours and minutes of signOutTime
    signOutTime = signOutTime.replace(hour=hours, minute=minutes)

    while True:
        currentDateTime = datetime.datetime.today()

        if currentDateTime >= signOutTime:
            signOut()
            break

        time.sleep(pollingrate)


# Runner
start()