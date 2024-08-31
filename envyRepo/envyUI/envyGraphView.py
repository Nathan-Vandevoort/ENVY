#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
envyGraphView.py: The QWidget which represents the envy graph view
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"

from PySide6.QtCore import Qt, QPointF, QThread, Signal, Slot
from PySide6.QtGui import QCursor, QPainter, QPen, QColor, QFont
from PySide6.QtWidgets import QWidget, QSizePolicy
from .nodeGraphSimulation import NodeGraphSimulation
from .nodeSolver import Node
import random


class EnvyGraphView(QWidget):
    graphViewAddNodeSignal = Signal(object)
    graphViewInertiaSignal = Signal(list)
    graphViewMouseMoveSignal = Signal(list)

    def __init__(self, parent=None, expanding=True):
        super(EnvyGraphView, self).__init__(parent)

        self.colorKey = {
            'Idle': [255, 255, 0],
            'Caching': [0, 255, 255],
            'Rendering': [0, 255, 0]
        }

        rect = self.geometry()
        self.bound = rect.bottomRight()
        self.bound = [self.bound.x(), self.bound.y()]

        # original Attributes
        self.originalWidth = self.width()
        self.originalHeight = self.height()
        self.zoomFactor = [1, 1]
        self.simStep = 0
        self.validationInterval = 100

        # Threading
        self.sim = NodeGraphSimulation(self.bound)
        self.simulationThread = QThread()
        self.sim.moveToThread(self.simulationThread)
        self.simulationThread.started.connect(self.sim.start)  # connect thread start signal to worker start signal
        self.sim.nodeGraphSimulationData.connect(
            self.updateSimulation)  # connect simulation signal to update simulation
        self.graphViewInertiaSignal.connect(self.sim.addForce)
        self.graphViewMouseMoveSignal.connect(self.sim.updateMouse)
        self.graphViewAddNodeSignal.connect(self.sim.addNode)  # connect add node signal
        self.simulationThread.start()

        self.setMouseTracking(True)

        self.tmp = 0
        self.mousePos = None
        self.nodeSize = 6

        # envyData
        self.envyData = {}

        # node attrs
        self.positions = []
        self.nodes = []
        self.nodeNames = {}

        # selectionAttrs
        self.boxSelectStart = None
        self.boxSelectEnd = None

        # mouse modifiers
        self.modifiers = None

        if expanding:
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.updateEnvyData()
        self.validateEnvyData()

    def paintEvent(self, event):
        # node drawing
        if len(self.nodes) > 0:

            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setFont(QFont("Arial", max(1, self.nodeSize * self.zoomFactor[0])))

            for i, node in enumerate(self.nodes):
                # color dependant on status
                color = self.colorKey[self.envyData[node.name]['status']]

                painter.setPen(
                    QPen(QColor(color[0], color[1], color[2]), self.nodeSize * self.zoomFactor[0], Qt.SolidLine,
                         Qt.RoundCap))
                pos = QPointF(self.positions[i][0] * self.zoomFactor[0], self.positions[i][1] * self.zoomFactor[1])
                painter.drawText(pos + QPointF(0, -self.nodeSize) * self.zoomFactor[0], self.nodes[i].name)
                painter.drawPoint(pos)

            painter.end()
        super().paintEvent(event)

    def mousePressEvent(self, event):
        modifiers = event.modifiers()
        self.modifiers = modifiers

        # add node button
        if event.button() == Qt.RightButton:
            localPos = event.position()
            newNode = Node(str(self.tmp))
            newNode.initialP = [localPos.x() / self.zoomFactor[0], localPos.y() / self.zoomFactor[1]]
            newNode.initialV = [random.uniform(-5, 5), random.uniform(-5, 5)]
            self.graphViewAddNodeSignal.emit(newNode)
            self.tmp += 1
            event.ignore()

        if event.button() == Qt.LeftButton:
            self.boxSelectStart = event.position()
            event.accept()

        if not self.mousePos and event.button() == Qt.LeftButton and self.modifiers == Qt.ControlModifier:
            self.mousePos = QCursor.pos()
            event.accept()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):

        # Check if the right button is pressed and the mouse position is valid
        if event.buttons() & Qt.LeftButton and self.mousePos and self.modifiers == Qt.ControlModifier:
            # Get the current mouse position
            currentPos = QCursor.pos()

            # Calculate the offset from the previous mouse position
            offset = self.mousePos - currentPos
            self.graphViewInertiaSignal.emit([offset.x() / self.zoomFactor[0], offset.y() / self.zoomFactor[1]])

            self.mousePos = currentPos

            event.ignore()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):

        self.mousePos = None

        if event.button() == Qt.RightButton:
            event.ignore()

        if event.button() == Qt.LeftButton:
            pass
        # if box selection

        # if not box selection

        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        self.zoomFactor = [self.width() / self.originalWidth, self.height() / self.originalHeight]
        super().resizeEvent(event)

    @Slot()
    def updateSimulation(self, simulationData):
        if self.simStep == 0:
            pass
            # self.updateEnvyData()
            # self.validateEnvyData()

        self.positions = simulationData.positions
        self.nodes = simulationData.nodes
        self.nodeNames = simulationData.nodeNames
        self.repaint()
        self.simStep = (self.simStep + 1) % self.validationInterval

    def validateEnvyData(self):  # ensure that nodes are being created and destroyed appropriately to the envy data
        for computer in self.envyData:
            if computer not in self.nodeNames:  # add node
                newNode = Node(computer)
                newNode.initialP = [random.uniform(0, (self.originalWidth) * self.zoomFactor[0]),
                                    random.uniform(0, (self.originalHeight) * self.zoomFactor[1])]
                newNode.initialV = [random.uniform(-5, 5), random.uniform(-5, 5)]
                self.graphViewAddNodeSignal.emit(newNode)

        for nodeName in self.nodeNames:

            if nodeName not in self.envyData:  # remove node
                pass

    def closeEvent(self, event):

        self.sim.stop()
        self.simulationThread.quit()
        self.simulationThread.wait()

    def updateEnvyData(self):
        parentWindow = self.parent()

        if parentWindow:  # ensure parent window exists
            self.envyData = parentWindow.getEnvyData()
