import sys
from qasync import QApplication, QEventLoop
from PySide6.QtWidgets import QVBoxLayout, QMainWindow, QTextEdit
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
import io
from envyRepo.envyLib import envy_logger
from envyRepo.envyCore.envyCore import Envy

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

        self.resize(800, 600)

        self.stream_display_widget = QTextEdit()
        self.stream_display_widget.setReadOnly(True)
        self.stream_display_widget.setFont(QFont('Courier New', 10))

        self.setCentralWidget(self.stream_display_widget)

        self.read_envy_stream_timer = QTimer(self)
        self.read_envy_stream_timer.timeout.connect(self.read_envy_stream)
        self.read_envy_stream_timer.start(50)

    def read_envy_stream(self):
        self.envy_stream.seek(self.envy_stream_seeker)
        new_text = self.envy_stream.readline()
        if new_text:
            self.stream_display_widget.append(new_text)
            self.envy_stream_seeker = self.envy_stream.tell()