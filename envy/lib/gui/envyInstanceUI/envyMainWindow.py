import sys, os
from qasync import QApplication, QEventLoop
from PySide6.QtWidgets import QVBoxLayout, QMainWindow, QTextEdit, QStackedWidget, QMenu, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QAction
import asyncio
from envy.lib.utils import logger
from envy.lib import Envy

NV = sys.modules.get('Envy_Functions')


class EnvyMainWindow(QMainWindow):
    def __init__(self, event_loop, application: QApplication, logger, stream):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.envy_stream = stream
        self.envy_stream_seeker = 0
        self.logger = logger
        self.qapp = application
        self.event_loop = event_loop
        self.envy = Envy(self.event_loop, logger=self.logger)
        self.event_loop.create_task(self.envy.start())

        self.resize(800, 400)

        self.central_widget = QStackedWidget(self)

        self.stream_display_widget = QTextEdit()
        self.stream_display_widget.setReadOnly(True)
        self.stream_display_widget.setFont(QFont('Courier New', 10))

        self.user_display_widget = QTextEdit()
        self.user_display_widget.setReadOnly(True)
        self.set_user_display()

        self.central_widget.addWidget(self.stream_display_widget)
        self.central_widget.addWidget(self.user_display_widget)
        self.central_widget.setCurrentIndex(1)
        self.setCentralWidget(self.central_widget)

        self.read_envy_stream_timer = QTimer(self)
        self.read_envy_stream_timer.timeout.connect(self.read_envy_stream)
        self.read_envy_stream_timer.start(50)

    def read_envy_stream(self):
        self.envy_stream.seek(self.envy_stream_seeker)
        new_text = self.envy_stream.readline()
        if new_text:
            self.stream_display_widget.append(new_text)
            self.envy_stream_seeker = self.envy_stream.tell()

    def set_user_display(self):
        username = os.getlogin()
        username = username.split('.')[0]

        self.user_display_widget.setAlignment(Qt.AlignHCenter)
        self.user_display_widget.setFont(QFont('Arial Black', 80))
        self.user_display_widget.setFontPointSize(160)
        self.user_display_widget.append('ENVY')

        self.user_display_widget.setFontPointSize(12)
        self.user_display_widget.append('Created By: Nathan Vandevoort')
        self.user_display_widget.append(f'Initialized By: {username}')
        self.user_display_widget.append('Sign out if needed')

    def enterEvent(self, event):
        self.central_widget.setCurrentIndex(0)
        return super().enterEvent(event)

    def leaveEvent(self, event):
        self.central_widget.setCurrentIndex(1)
        return super().leaveEvent(event)

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
