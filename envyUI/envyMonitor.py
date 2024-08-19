#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
envyMonitor.py: An object intended to be run in a separate thread which maintains data about envy instances
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"

from PySide6.QtCore import Slot, QCoreApplication, Signal, QObject
import time
import os
from global_config import Globals


ENVYPATH = Globals.ENVYPATH


class EnvyMonitor(QObject):  # intended to be run on a separate thread which monitors envy things

    dataUpdated = Signal(dict)

    def __init__(self):
        super(EnvyMonitor, self).__init__()

        self.computers = {}  # A dictionary which contains computer name and associated information
        self.running = False

    @Slot()
    def updateComputers(self):
        envyLogsPath = ENVYPATH + 'EnvyLogs/'

        # check if envy logs path exists
        if not os.path.exists(envyLogsPath):
            raise FileNotFoundError(f'Envy Logs Path does not exist at {envyLogsPath}')

        envyLogDirs = os.listdir(envyLogsPath)

        tempComputersDict = {}

        for logDir in envyLogDirs:

            computerLogPath = envyLogsPath + logDir + '/'

            name = logDir
            status = None
            job = None
            logPath = computerLogPath

            statusPath = f'{computerLogPath}/STATUS.txt'

            # check if status path exists
            if not os.path.exists(statusPath):
                continue

            # get status from file
            with open(statusPath, 'r') as statusFile:
                status = statusFile.read()

            tempComputersDict[logDir] = {
                'name': name,
                'status': status,
                'job': job,
                'logPath': logPath
            }

        self.computers.clear()
        self.computers = tempComputersDict

    @Slot()
    def start(self):
        self.running = True
        while self.running:
            self.updateComputers()
            self.dataUpdated.emit(self.computers)
            QCoreApplication.processEvents()
            time.sleep(10)

    @Slot()
    def stop(self):
        self.running = False

    def getComputers(self):
        return self.computers
