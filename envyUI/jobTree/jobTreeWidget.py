import sys
import prep_env
import config_bridge
from PySide6.QtWidgets import QTreeView, QMainWindow, QApplication, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import QTimer, QPoint, Qt, Signal, Slot
from envyJobs import jobTree
from envyDB import db
from jobTreeModel import JobTreeModel
from networkUtils.message_purpose import Message_Purpose as MP
from networkUtils import message as m


class JobTreeWidget(QTreeView):

    dirty_job_element = Signal(object)
    finish_job_element = Signal(object)

    def __init__(self, parent=None, logger=None):
        super().__init__(parent)

        self.data_base = None
        self.job_tree = None
        self.model = None
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)
        self.configure_tree()

    def configure_tree(self):
        self.data_base = db.DB()
        self.data_base.start()
        self.job_tree = jobTree.JobTree()
        self.job_tree.enable_read_only()
        self.job_tree.skip_complete_tasks = False
        self.job_tree.skip_complete_allocations = False
        self.job_tree.set_db(self.data_base)
        self.job_tree.build_from_db()

        self.model = JobTreeModel(self.job_tree.root)
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
        path = selected_item.get_absolute_path()

        new_message = m.FunctionMessage('Finish_Job_element')
        if len(path) == 1:
            new_message.set_function('mark_job_as_finished')
            new_message.set_target(MP.SERVER)
            new_message.format_arguments(path[0])

        if len(path) == 2:
            new_message.set_function('mark_allocation_as_finished')
            new_message.set_target(MP.SERVER)
            new_message.format_arguments(path[1])

        if len(path) == 3:
            new_message.set_function('mark_task_as_finished')
            new_message.set_target(MP.SERVER)
            new_message.format_arguments(path[2])

        self.finish_job_element.emit(new_message)

    def mark_job_as_finished(self, job_id: int) -> None:
        pass

def convert_anytree_to_jobitem(anytree_node, parent_item=None):
    node_type = anytree_node.node_type
    new_item = JobItem(parent=parent_item)
    if node_type == 'Job':
        new_item.set_name(anytree_node.job_name)
        new_item.set_ID(anytree_node.name)
        new_item.set_status(anytree_node.status)
        new_item.set_progress(anytree_node.progress)
        new_item.set_computer('N/A')

    if node_type == 'Allocation':
        children = anytree_node.children
        start_frame_task = children[0]
        end_frame_task = children[-1]

        new_item.set_name(f'{start_frame_task.frame}-{end_frame_task.frame}')
        new_item.set_ID(anytree_node.name)
        new_item.set_status(anytree_node.status)
        new_item.set_progress(anytree_node.progress)
        new_item.set_computer(anytree_node.computer)

    if node_type == 'Task':
        new_item.set_name(str(anytree_node.frame))
        new_item.set_ID(anytree_node.name)
        new_item.set_status(anytree_node.status)
        new_item.set_progress(anytree_node.progress)
        new_item.set_computer(anytree_node.computer)

    if node_type == 'root':
        new_item.set_name('root')
        new_item.set_ID(-1)
        new_item.set_progress(0)

    if parent_item is not None:
        parent_item.appendChild(new_item)

    for child in anytree_node.children:
        convert_anytree_to_jobitem(child, parent_item=new_item)

    return new_item

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