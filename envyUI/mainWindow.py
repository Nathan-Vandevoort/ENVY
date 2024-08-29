#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
mainWindow.py: A wrapper for the QMainWindow function to prepare it to be the host window for the envy UI
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"

import prep_env
from PySide6.QtCore import Qt, QRect, QEvent, QPoint, QThread
from PySide6.QtGui import QCursor, QVector2D, QTransform
from PySide6.QtWidgets import QMainWindow, QWidget, QSizeGrip, QVBoxLayout, QHBoxLayout, QTextEdit, QTreeView, QSplitter
import console_widget
from jobTree import jobTreeWidget

class MainWindow(QMainWindow):

    def __init__(self, event_loop):
        super().__init__()

        # set the window flag to frameless
        #self.setWindowFlags(Qt.FramelessWindowHint)

        # Envy backend
        self.event_loop = event_loop


        # mouse Attrs
        self.mousePos = None
        self.initialPos = None

        # settings

        # Widgets
        self.viewport_widget = QTextEdit('Viewport')

        right_layout = QVBoxLayout()
        self.job_view_widget = jobTreeWidget.JobTreeWidget()
        right_layout.addWidget(self.job_view_widget)

        self.console_widget = console_widget.ConsoleWidget(event_loop=self.event_loop)
        right_layout.addWidget(self.console_widget)

        right_container = QWidget()
        right_container.setLayout(right_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.viewport_widget)
        splitter.addWidget(right_container)

        central_widget = QWidget()
        central_layout = QHBoxLayout(central_widget)
        central_layout.addWidget(splitter)
        self.setCentralWidget(central_widget)

        self.job_view_widget.finish_job_element.connect(self.console_widget.send_message)  # job view -> console when user marks job as finished

        self.console_widget.jobs_finish_job.connect(self.job_view_widget.mark_job_as_finished)  # console -> job view. when a job is marked finished update the view

    def mousePressEvent(self, event):

        # check if right click is pressed
        if event.button() == Qt.RightButton:
            self.mousePos = QCursor.pos()
            self.initialPos = self.pos()
            event.accept()

        elif event.button() == Qt.MiddleButton:
            self.mousePos = QCursor.pos()
            event.accept()

    def closeEvent(self, event):

        children = self.findChildren(QWidget)

        for child in children:
            child.close()

        super().closeEvent(event)