#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
mainWindow.py: A wrapper for the QMainWindow function to prepare it to be the host window for the envy UI
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"

import envy.lib.prep_env
import asyncio, sys
from PySide6.QtCore import Qt, QRect, QEvent, QPoint, QThread
from PySide6.QtGui import QCursor, QVector2D, QTransform
from PySide6.QtWidgets import QMainWindow, QWidget, QSizeGrip, QVBoxLayout, QHBoxLayout, QTextEdit, QTreeView, QSplitter, QApplication
from envy.lib.gui import console_widget
from envy.lib.gui.jobTree import jobTreeWidget
from envy.lib.gui.viewport import viewportWidget


class MainWindow(QMainWindow):

    def __init__(self, event_loop, application: QApplication):
        super().__init__()

        # set the window flag to frameless
        #self.setWindowFlags(Qt.FramelessWindowHint)
        self.qapp = application

        # Envy backend
        self.event_loop = event_loop


        # mouse Attrs
        self.mousePos = None
        self.initialPos = None

        #  window settings
        self.setWindowTitle("Envy Console")
        self.resize(1600, 600)

        # settings

        # Widgets
        screen_geometry = self.qapp.primaryScreen().geometry()
        self.viewport_widget = viewportWidget.ViewportWidget(width=750, height=550)
        self.job_tree_widget = jobTreeWidget.JobTreeWidget()
        self.console_widget = console_widget.ConsoleWidget(event_loop=self.event_loop)

        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(self.job_tree_widget)
        right_splitter.addWidget(self.console_widget)
        right_splitter.setSizes([450, 150])

        right_container = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(right_splitter)
        right_container.setLayout(right_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.viewport_widget)
        splitter.addWidget(right_container)
        splitter.setSizes([800, 800])

        central_widget = QWidget()
        central_layout = QHBoxLayout(central_widget)
        central_layout.addWidget(splitter)
        self.setCentralWidget(central_widget)

        # --------------------------- Connections -----------------------------------#

        self.job_tree_widget.finish_job_element.connect(self.console_widget.send_message)  # job view -> console when user marks job as finished

        self.console_widget.jobs_finish_job.connect(self.job_tree_widget.controller.mark_job_as_finished)  # console -> job view. when a job is marked finished update the view
        self.console_widget.jobs_sync_job.connect(self.job_tree_widget.controller.sync_job)  # console -> job tree. When the server ingests a new job send a signal to the console to sync that new job
        self.console_widget.jobs_start_task.connect(self.job_tree_widget.controller.mark_task_as_started)  # console -> job tree. Tells the job tree that a client has started a different task
        self.console_widget.jobs_finish_task.connect(self.job_tree_widget.controller.mark_task_as_finished)  # console -> job tree. Tells the tree that a task has been finished
        self.console_widget.jobs_start_allocation.connect(self.job_tree_widget.controller.mark_allocation_as_started)  # console -> job tree. Tells the tree a new allocation has been started
        self.console_widget.jobs_finish_allocation.connect(self.job_tree_widget.controller.mark_allocation_as_finished)  # console -> job tree. tells the tree that an allocation has been finished
        self.console_widget.jobs_fail_task.connect(self.job_tree_widget.controller.mark_task_as_failed)  # console -> jobTree. marks the task as failed and provides the reason
        self.console_widget.jobs_fail_allocation.connect(self.job_tree_widget.controller.mark_allocation_as_failed)  # console -> jobTree. marks the allocation as failed and provides the reason
        self.console_widget.jobs_update_allocation_progress.connect(self.job_tree_widget.controller.update_allocation_progress)  # console -> jobTree updates the progress of an allocation

        self.console_widget.register_client.connect(self.viewport_widget.controller.register_client)  # console -> viewport telling the viewport hey I just got a new client
        self.console_widget.unregister_client.connect(self.viewport_widget.controller.unregister_client)  # console -> viewport telling the viewport hey I just lost connection to a client
        self.console_widget.set_clients.connect(self.viewport_widget.controller.set_clients)  # console -> viewport telling the viewport to sync to new clients

        self.console_widget.disconnected_with_server.connect(self.viewport_widget.controller.disconnected_with_server)  # console -> viewport, saying hey I'm disconnected from the server
        self.console_widget.disconnected_with_server.connect(self.job_tree_widget.controller.disconnected_with_server)  # console -> jobTree, saying hey I'm disconnected from the server
        self.console_widget.connected_with_server.connect(self.viewport_widget.controller.connected_with_server)  # console -> viewport, saying hey I'm connected with the server
        self.console_widget.connected_with_server.connect(self.job_tree_widget.controller.connected_with_server)  # console -> jobTree, saying hey I'm connected with the server

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

        tasks = [t for t in asyncio.all_tasks(self.event_loop) if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        self.event_loop.stop()

        children = self.findChildren(QWidget)

        for child in children:
            child.close()

        super().closeEvent(event)
        quit(0)