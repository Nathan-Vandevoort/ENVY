import sys
import prep_env
import config_bridge
from PySide6.QtWidgets import QTreeView, QMainWindow, QApplication, QMenu
from PySide6.QtGui import QAction, QFont
from PySide6.QtCore import QTimer, QPoint, Qt, Signal, Slot
from envyUI.jobTree import jobTreeController
from envyJobs import jobTreeAbstractItemModel
from networkUtils.message_purpose import Message_Purpose as MP
from networkUtils import message as m
from envyDB import db


class JobTreeWidget(QTreeView):

    dirty_job_element = Signal(object)
    finish_job_element = Signal(object)

    def __init__(self, parent=None, logger=None):
        super().__init__(parent=parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setSelectionMode(QTreeView.ExtendedSelection)
        self.customContextMenuRequested.connect(self.open_context_menu)

        self.db = db.DB()
        self.db.start()
        self.model = jobTreeAbstractItemModel.JobTreeItemModel()
        self.model.enable_read_only()
        self.model.skip_complete_tasks = False
        self.model.skip_complete_allocations = False
        self.model.set_db(self.db)
        self.model.build_from_db()

        self.controller = jobTreeController.JobTreeController(self.model)
        self.setModel(self.model)

        # display settings
        #   resize header elements
        self.header().resizeSection(0, 200)
        self.header().resizeSection(1, 80)
        self.header().resizeSection(2, 80)
        self.header().resizeSection(3, 80)

        #   font
        font = QFont('Segoe UI', 10)
        self.setFont(font)

        #   alternating colors
        self.setAlternatingRowColors(True)


    def open_context_menu(self, position: QPoint):
        indices = self.selectedIndexes()

        valid_items = []
        for index in indices:
            if not index.isValid():
                continue
            if self.model.getItem(index) in valid_items:
                continue
            valid_items.append(self.model.getItem(index))

        context_menu = QMenu(self)
        dirty_action = QAction('Dirty', self)
        finish_action = QAction('Finish', self)
        select_workers_action = QAction('Select Workers', self)

        context_menu.addAction(dirty_action)
        context_menu.addAction(finish_action)
        context_menu.addAction(select_workers_action)

        dirty_action.triggered.connect(lambda: self.dirty_action_triggered(valid_items))
        finish_action.triggered.connect(lambda: self.finish_action_triggered(valid_items))
        select_workers_action.triggered.connect(lambda: self.select_workers_action_triggered(valid_items))

        context_menu.exec_(self.viewport().mapToGlobal(position))

    def dirty_action_triggered(self, items):
        for selected_item in items:
            path = selected_item.get_absolute_path()

    def finish_action_triggered(self, items):
        for selected_item in items:
            job_type = selected_item.node_type

            new_message = m.FunctionMessage('Finish_Job_element')
            if job_type == 'Job':
                new_message.set_function('mark_job_as_finished')
                new_message.set_target(MP.SERVER)
                new_message.format_arguments(selected_item.name, from_console=True)

            if job_type == 'Allocation':
                new_message.set_function('mark_allocation_as_finished')
                new_message.set_target(MP.SERVER)
                new_message.format_arguments(selected_item.name, from_console=True)

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