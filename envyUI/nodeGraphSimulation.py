#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
nodeGraphSimulation.py: The QObject which runs nodeSolver.py
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"

from PySide6.QtCore import QObject, Signal, QCoreApplication, Slot
from .nodeSolver import NodeSolver
import time


class NodeGraphSimulation(QObject):
    nodeGraphSimulationData = Signal(object)

    def __init__(self, bound):
        super().__init__()
        self.sim = NodeSolver(bound)
        self.refreshRate = .01
        self.running = False
        self.highestSpeed = 0

    @Slot()
    def start(self):
        self.running = True
        self.update()

    @Slot()
    def stop(self):
        self.running = False

    def update(self):

        # loop
        while self.running:
            self.sim.update()
            simulationData = self.sim.getSimulationData()
            self.nodeGraphSimulationData.emit(simulationData)
            self.highestSpeed = simulationData.highestSpeed
            self.calculateRefreshRate()
            QCoreApplication.processEvents()  # to allow this to receive signals

            time.sleep(self.refreshRate)

    @Slot()
    def addNode(self, nodeInformation):
        name = nodeInformation.name
        P = nodeInformation.initialP
        V = nodeInformation.initialV
        self.sim.addNode(name, P, V)

    @Slot()
    def getNodes(self):
        return self.sim.NODENAMES

    @Slot()
    def addForce(self, force=None):
        if force is None:
            force = [0, 0]

        self.sim.addForce(force)

    @Slot()
    def setRefreshRate(self, rate):
        self.refreshRate = rate

    @Slot()
    def updateMouse(self, mousePos=None):
        if mousePos is None:
            mousePos = [0, 0]

        self.sim.updateMouse(mousePos)

    def calculateRefreshRate(self):
        """
        clamp between lowBound and HighBound
        if lowBound then increase refresh rate to .05 at max
        if highBound then decrease to .01 at min

        if sudden speed increase set rate to high

        if decrease then gradually decrease rate
        """
        lowBound = 0
        highBound = 1
        lowRate = .1
        highRate = .01

        speed = max(lowBound, min(highBound, self.highestSpeed))

        speed = (1 - (speed / highBound)) ** 3

        newRate = max(highRate, speed * lowRate)

        if newRate < self.refreshRate:
            self.refreshRate = newRate

        else:
            self.refreshRate = self.refreshRate + .001
