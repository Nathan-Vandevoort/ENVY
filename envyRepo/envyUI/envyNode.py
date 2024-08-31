#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
envyNode: The representation of a floating window or node in the envy UI
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"


from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QMdiSubWindow


class EnvyNode(QMdiSubWindow):

    def __init__(self):
        super(EnvyNode, self).__init__()

        self.nodeMovePos = None
        self.initialPos = None

        self.floatWidth = float(self.width())
        self.floatHeight = float(self.height())

        # arbitrary Attributes
        self.envyData = {}

        self.modifiers = None

    def mousePressEvent(self, event):

        modifiers = event.modifiers()
        self.modifiers = modifiers

        # check if ctrl + LMB is pressed
        if event.button() == Qt.LeftButton and modifiers == Qt.ControlModifier:
            self.nodeMovePos = QCursor.pos()
            self.initialPos = self.pos()
            # self.update()
            event.accept()

    def mouseMoveEvent(self, event):

        # Check if the right button is pressed and the mouse position is valid
        if event.buttons() == Qt.LeftButton and self.nodeMovePos and self.modifiers == Qt.ControlModifier:
            # Get the current mouse position
            currentPos = QCursor.pos()

            # Calculate the offset from the previous mouse position
            offset = self.initialPos - self.nodeMovePos

            # Move the window by the offset
            self.move(currentPos + offset)

            # Accept the event
            event.accept()

    def mouseReleaseEvent(self, event):

        # check if button is right click
        if event.button() == Qt.LeftButton:
            # reset the mouse position
            self.nodeMovePos = None
            self.initialPos = None
            event.accept()

        self.modifiers = None

    def widget(self):
        return super().widget()

    def updateEnvyData(self, envyData):
        self.envyData = envyData

    def getEnvyData(self):
        return self.envyData
