import sys
from qasync import QApplication, QEventLoop
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QTextEdit, QMainWindow, QMessageBox
from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QFont
from envy.lib.core import consoleCore
import io
from envy.lib.utils import logger
from queue import Queue
import logging


class ConsoleWidget(QWidget):

    jobs_sync_job = Signal(
        float
    )  # these are floats because ittie bittie 4Byte ints cant hold my raw power. Remember to cast them to int in the slot

    jobs_finish_job = Signal(float)
    jobs_finish_allocation = Signal(float)
    jobs_finish_task = Signal(float)

    jobs_add_dependency = Signal(str)

    jobs_fail_task = Signal(tuple)
    jobs_fail_allocation = Signal(tuple)

    jobs_update_allocation_progress = Signal(tuple)

    jobs_start_allocation = Signal(tuple)
    jobs_start_task = Signal(tuple)

    register_client = Signal(tuple)
    unregister_client = Signal(str)
    set_clients = Signal(dict)

    disconnected_with_server = Signal()
    connected_with_server = Signal()

    def __init__(self, parent=None, event_loop=None):
        super().__init__(parent)

        self.event_loop = event_loop

        self.input_queue = Queue(maxsize=0)
        self.output_stream = io.StringIO()
        self.input_stream = io.StringIO()
        self.output_stream_seeker = 0
        self.logger = envy_logger.get_logger(self.output_stream, html=True, level=logging.INFO)

        self.envy_console = consoleCore.Console(
            self.event_loop, input_queue=self.input_queue, stand_alone=False, logger=self.logger, console_widget=self
        )

        self.text_input_widget = QLineEdit(self)
        self.text_input_widget.returnPressed.connect(self.send_input)

        self.text_output_widget = QTextEdit(self)
        self.text_output_widget.setReadOnly(True)
        layout = QVBoxLayout()

        layout.addWidget(self.text_output_widget)
        layout.addWidget(self.text_input_widget)

        self.read_output_timer = QTimer(self)
        self.read_output_timer.timeout.connect(self.read_output)
        self.read_output_timer.start(50)

        self.coroutines = []

        envy_console_task = self.event_loop.create_task(self.envy_console.start())
        envy_console_task.set_name('Envy console task')
        self.coroutines.append(envy_console_task)

        self.setLayout(layout)

        font = QFont('Courier New', 8)
        self.setFont(font)

    def send_input(self):
        input_string = self.text_input_widget.text() + '\n'
        self.input_queue.put(input_string)
        self.text_input_widget.clear()

    def read_output(self):
        self.output_stream.seek(self.output_stream_seeker)
        new_text = self.output_stream.readline()
        if new_text:
            self.text_output_widget.append(new_text)
            self.output_stream_seeker = self.output_stream.tell()

    def show_confirmation(self, message: str):
        reply = QMessageBox.question(self, 'Confirmation', message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == 65536:
            return False
        else:
            return True

    def closeEvent(self, event):
        self.read_output_timer.stop()

        for task in self.coroutines:
            task.cancel()

        super().closeEvent(event)

    def send_message(self, message):
        self.envy_console.send(message)


if __name__ == '__main__':

    class MainWindow(QMainWindow):
        def __init__(self, event_loop=None):
            super().__init__()
            self.event_loop = event_loop
            self.console_widget = ConsoleWidget(self, event_loop=self.event_loop)
            self.setCentralWidget(self.console_widget)

    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    window = MainWindow(event_loop=loop)
    window.show()
    loop.run_forever()
    sys.exit(app.exec())
