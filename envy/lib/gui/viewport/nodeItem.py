from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsSceneHoverEvent
from PySide6.QtGui import QBrush, QPen, QColor, QHoverEvent
from PySide6.QtCore import Qt
from envy.lib.jobs import enums
import numpy as np
import random

class NodeItem(QGraphicsEllipseItem):
    def __init__(self, radius, computer):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)

        # -------------------------------------- Node Attributes ----------------------------------- #
        self._computer = computer
        self._job = None
        self._allocation = None
        self._task = None
        self._status = enums.Status.IDLE
        self.tile_index = -1

        # -------------------------------------- Appearance Attributes -------------------------------- #
        self._color = Qt.blue
        self.brush = QBrush(self._color)
        self.pen = QPen(self._color)
        self.setBrush(self.brush)
        self.setPen(self.pen)
        self.size = 2 * radius
        self.rest_size = 2 * radius
        self.target_size = self.rest_size

        # -------------------------------------- Physics Attributes ----------------------------------- #
        self.damp = 1
        self.mag = 5
        self.v = np.array([random.random() * self.mag, random.random() * self.mag]).astype(float)
        self.P = np.array([0, 0]).astype(float)

        # -------------------------------------- QGraphicsItem Attributes ----------------------------------- #
        self.setAcceptHoverEvents(True)
        self.hovered = False

    # -------------------------- Hover events ------------------------------#
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        self.color = Qt.yellow
        self.hovered = True
        self.target_size = 3 * self.rest_size
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        self.color = Qt.blue
        self.hovered = False
        self.target_size = self.rest_size
        super().hoverLeaveEvent(event)

    def setX(self, value):
        super().setX(value)
        self.P[0] = value

    def setY(self, value):
        super().setY(value)
        self.P[1] = value

    @property
    def computer(self):
        return self._computer

    @computer.setter
    def computer(self, value):
        self._computer = value

    @property
    def job(self):
        return self._job

    @job.setter
    def job(self, value):
        self._job = value

    @property
    def allocation(self):
        return self._allocation

    @allocation.setter
    def allocation(self, value):
        self._allocation = value

    @property
    def task(self):
        return self._task

    @task.setter
    def task(self, value):
        self._task = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value: QColor):
        self._color = value

        self.pen.setColor(value)
        self.brush.setColor(value)
        self.setPen(self.pen)
        self.setBrush(self.brush)

    def boundingRect(self):
        return self.rect()

    def add_size(self):
        self.prepareGeometryChange()
        self.size += 4
        self.setRect(-self.size / 2, -self.size / 2, self.size, self.size)

    def subtract_size(self):
        self.prepareGeometryChange()
        self.size -= 2
        self.setRect(-self.size / 2, -self.size / 2, self.size, self.size)

    def __repr__(self):
        return self._computer