import sys
import prep_env
import config_bridge
from PySide6.QtWidgets import QTreeView, QMainWindow, QApplication, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import QTimer, QPoint, Qt, Signal, Slot
from envyUI.jobTree import jobTreeController
from envyUI.jobTree import jobTreeModel
from networkUtils.message_purpose import Message_Purpose as MP
from networkUtils import message as m


class JobTreeWidget(QTreeView):

    dirty_job_element = Signal(object)
    finish_job_element = Signal(object)

    def __init__(self, parent=None, logger=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)
        self.model = jobTreeModel.JobTreeModel()
        self.controller = jobTreeController.JobTreeController(self.model)
        self.setModel(self.model)

    def open_context_menu(self, position: QPoint):
        index = self.indexAt(position)
        if not index.isValid():
            return

        context_menu = QMenu(self)
        dirty_action = QAction('Dirty', self)
        finish_action = QAction('Finish', self)
        select_workers_action = QAction('Select Workers', self)

        context_menu.addAction(dirty_action)
        context_menu.addAction(finish_action)
        context_menu.addAction(select_workers_action)

        dirty_action.triggered.connect(lambda: self.dirty_action_triggered(index))
        finish_action.triggered.connect(lambda: self.finish_action_triggered(index))
        select_workers_action.triggered.connect(lambda: self.select_workers_action_triggered(index))

        context_menu.exec_(self.viewport().mapToGlobal(position))

    def dirty_action_triggered(self, index):
        if not index.isValid():
            return
        selected_item = self.model.getItem(index)
        path = selected_item.get_absolute_path()

    def finish_action_triggered(self, index):
        if not index.isValid():
            return
        selected_item = self.model.getItem(index)
        job_type = selected_item.node_type

        new_message = m.FunctionMessage('Finish_Job_element')
        if job_type == 'Job':
            new_message.set_function('mark_job_as_finished')
            new_message.set_target(MP.SERVER)
            new_message.format_arguments(selected_item.name)

        if job_type == 'Allocation':
            new_message.set_function('mark_allocation_as_finished')
            new_message.set_target(MP.SERVER)
            new_message.format_arguments(selected_item.name)

        if job_type == 'Task':
            new_message.set_function('mark_task_as_finished')
            new_message.set_target(MP.SERVER)
            new_message.format_arguments(selected_item.name)

        self.finish_job_element.emit(new_message)

if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self, event_loop=None):
            super().__init__()
            self.tree_widget = JobTreeWidget(parent=self)
            self.setCentralWidget(self.tree_widget)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())