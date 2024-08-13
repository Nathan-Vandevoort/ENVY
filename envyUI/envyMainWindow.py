#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
envyMainWindow.py: A wrapper for the QMainWindow function to prepare it to be the host window for the envy UI
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"


from PySide6.QtCore import Qt, QRect, QEvent, QPoint, QThread
from PySide6.QtGui import QCursor, QVector2D, QTransform
from PySide6.QtWidgets import QMainWindow, QWidget, QSizeGrip, QMdiArea
from .envyNode import EnvyNode
from .envyMonitor import EnvyMonitor


class EnvyMainWindow(QMainWindow):

    def __init__(self):
        super(EnvyMainWindow, self).__init__()

        # set the window flag to frameless
        self.setWindowFlags(Qt.FramelessWindowHint)

        # mouse Attrs
        self.mousePos = None
        self.initialPos = None

        # create MdiArea
        self.mdiArea = QMdiArea()
        self.setCentralWidget(self.mdiArea)

        # nodes dict
        self.nodes = {}

        # resizeGrips
        self.resize(800, 600)
        self.gripSize = 16

        # grips
        self.topLeftGrip = QSizeGrip(self)
        self.topLeftGrip.resize(self.gripSize, self.gripSize)

        self.topRightGrip = QSizeGrip(self)
        self.topRightGrip.resize(self.gripSize, self.gripSize)
        self.topRightGrip.move(self.width() - self.gripSize, 0)

        self.bottomLeftGrip = QSizeGrip(self)
        self.bottomLeftGrip.resize(self.gripSize, self.gripSize)
        self.bottomLeftGrip.move(0, self.height() - self.gripSize)

        self.bottomRightGrip = QSizeGrip(self)
        self.bottomRightGrip.resize(self.gripSize, self.gripSize)
        self.bottomRightGrip.move(self.width() - self.gripSize, self.height() - self.gripSize)

        # settings
        self.scrollSensitivity = 1

        # create Envy Monitor thread
        self.EnvyMonitor = EnvyMonitor()
        self.EnvyMonitorThread = QThread()
        self.EnvyMonitor.moveToThread(self.EnvyMonitorThread)
        self.EnvyMonitorThread.started.connect(self.EnvyMonitor.start)
        self.EnvyMonitorThread.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # move grips to correct positions

        # dont need to move top left grip
        self.topRightGrip.move(self.width() - self.gripSize, 0)
        self.bottomLeftGrip.move(0, self.height() - self.gripSize)
        self.bottomRightGrip.move(self.width() - self.gripSize, self.height() - self.gripSize)

    def mousePressEvent(self, event):

        # check if right click is pressed
        if event.button() == Qt.RightButton:
            self.mousePos = QCursor.pos()
            self.initialPos = self.pos()
            event.accept()

        elif event.button() == Qt.MiddleButton:
            self.mousePos = QCursor.pos()
            event.accept()

    def wheelEvent(self, event):

        # scale nodes
        cursorPos = QVector2D(event.position())  # get cursor pos
        scrollStrength = 1.1 if event.angleDelta().y() > 0 else .9  # get direction of scaling
        scrollStrength *= self.scrollSensitivity  # multiply by scroll sensitivity

        # iterate over nodes and scale
        for w in self.nodes:
            node = self.nodes[w]
            width = node.floatWidth
            height = node.floatHeight

            # transform
            topLeftCorner = QPoint(node.pos().x(), node.pos().y())
            bottomRightCorner = QPoint(node.pos().x() + width, node.pos().y() + height)  # using coords because rect doesnt work in a way that makes sense. It only stores width and height
            transform = QTransform()
            transform.translate(cursorPos.x(), cursorPos.y())
            transform.scale(scrollStrength, scrollStrength)
            transform.translate(-cursorPos.x(), -cursorPos.y())

            # apply transforms
            topLeftCorner = transform.map(topLeftCorner)
            bottomRightCorner = transform.map(bottomRightCorner)

            rect = QRect()
            rect.setCoords(topLeftCorner.x(), topLeftCorner.y(), bottomRightCorner.x(), bottomRightCorner.y())
            node.setGeometry(rect)
            node.floatWidth *= scrollStrength
            node.floatHeight *= scrollStrength

    def mouseMoveEvent(self, event):

        # Check if the right button is pressed and the mouse position is valid
        if event.buttons() & Qt.RightButton and self.mousePos:
            # Get the current mouse position
            currentPos = QCursor.pos()

            # Calculate the offset from the previous mouse position
            offset = self.initialPos - self.mousePos

            # Move the window by the offset
            self.move(currentPos + offset)

            # Accept the event
            event.accept()

        if event.buttons() & Qt.MiddleButton and self.mousePos:

            # Get the current mouse position
            currentPos = QCursor.pos()

            # Calculate the offset from the previous mouse position
            moveAmnt = currentPos - self.mousePos

            # iterate over nodes and move them
            for w in self.nodes:
                widget = self.nodes[w]
                widget.move(widget.pos() + moveAmnt)

            # Update the mouse position
            self.mousePos = currentPos

            # Accept the event
            event.accept()

    def mouseReleaseEvent(self, event):

        # check if button is right click
        if event.button() == Qt.RightButton:

            # reset the mouse position
            self.mousePos = None
            self.initialPos = None
            event.accept()

        # check if button is middle click
        elif event.button() == Qt.MiddleButton:

            # reset the mouse position
            self.mousePos = None
            event.accept()

    def eventFilter(self, source, event):

        # the following code allows the window to be moved and panned around even if the mouse is on a subwidget
        if isinstance(source, EnvyNode) and event.type() == QEvent.MouseButtonPress:

            if event.button() == Qt.MiddleButton:
                self.mousePressEvent(event)
                return True

            if event.button() == Qt.RightButton:
                self.mousePressEvent(event)
                return True

        if isinstance(source, EnvyNode) and event.type() == QEvent.MouseMove and self.mousePos:
            self.mouseMoveEvent(event)
            return True

        if isinstance(source, EnvyNode) and event.type() == QEvent.MouseButtonRelease and self.mousePos:
            self.mouseReleaseEvent(event)
            return True

        return super().eventFilter(source, event)

    def addNode(self, widget, name):

        if not isinstance(widget, QWidget):
            raise TypeError(f"{widget} is not of type QWidget")

        elif name in self.nodes:
            raise NameError(f"{name} already exists in widgets dict")

        # add to nodes dict
        node = EnvyNode()
        node.setWidget(widget)
        node.setWindowFlags(Qt.FramelessWindowHint)
        node.installEventFilter(self)

        # connect zoom event
        self.nodes[name] = node

        # adds a widget to mdiArea
        self.mdiArea.addSubWindow(node)

        # connect envy data signal to nv node slot
        self.EnvyMonitor.dataUpdated.connect(node.updateEnvyData)

    def removeNode(self, name):

        if name not in self.nodes:
            raise NameError(f"{name} does not exist in widgets dict")

        self.nodes[name].deleteLater()

        # remove from nodes dict
        del self.nodes[name]

    def closeEvent(self, event):

        children = self.findChildren(QWidget)

        for child in children:
            child.close()

        self.EnvyMonitor.stop()
        self.EnvyMonitorThread.quit()
        self.EnvyMonitorThread.wait()

        super().closeEvent(event)
