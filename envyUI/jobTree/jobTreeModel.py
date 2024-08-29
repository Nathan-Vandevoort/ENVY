import sys
import prep_env
import config_bridge
from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex
from PySide6.QtWidgets import QMainWindow, QApplication, QTreeView
from envyDB import db
from envyJobs import jobTree
from envyJobs.jobItem import JobItem

class JobTreeModel(QAbstractItemModel):
    def __init__(self, root, parent=None):
        super(JobTreeModel, self).__init__(parent)
        self._rootItem = root
        self.header = ['Job Name', 'Progress', 'Status', 'Computer']

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return self._rootItem.child_count()
        return parent.internalPointer().child_count()

    def columnCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return self._rootItem.columnCount()
        return parent.internalPointer().columnCount()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = self.getItem(index)
        parentItem = childItem.parent
        if not parentItem or parentItem == self._rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid() and parent.column() != 0:
            return QModelIndex()

        parentItem = self.getItem(parent)
        if not parentItem:
            return QModelIndex()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)

        return QModelIndex()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[section]
        return None

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        if role != Qt.EditRole or orientation != Qt.Horizontal:
            return False

        result = self._rootItem.set_data(section, value)
        return result

    def getItem(self, index) -> JobItem:
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self._rootItem

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or (role != Qt.DisplayRole and role != Qt.EditRole):
            return None
        item = self.getItem(index)
        return item.data(index.column())

    def item_from_path(self, path: tuple) -> (JobItem, None):
        path_split_length = len(path)

        job = self.get_job_from_id(int(path[0]))

        if job is None:
            return None

        if path_split_length == 1:
            return job

        allocation = self.get_allocation_from_id(job, int(path[1]))

        if allocation is None:
            return None

        if path_split_length == 2:
            return allocation

        task = self.get_task_from_id(allocation, int(path[2]))

        if task is None:
            return None

        return task

    def get_job_from_id(self, ID: int) -> (JobItem, None):
        for job in self._rootItem._children:
            if job.ID == ID:
                return job
        return None

    def get_allocation_from_id(self, job: JobItem, ID: int) -> (JobItem, None):
        for allocation in job._children:
            if allocation.ID == ID:
                return allocation
        return None

    def get_task_from_id(self, allocation: JobItem, ID: int) -> (JobItem, None):
        for task in allocation._children:
            if task.ID == ID:
                return task
        return None


if __name__ == '__main__':

    data_base = db.DB()
    data_base.start()
    job_tree = jobTree.JobTree()
    job_tree.enable_read_only()
    job_tree.skip_complete_tasks = False
    job_tree.skip_complete_allocations = False
    job_tree.set_db(data_base)
    job_tree.build_from_db()

    def convert_anytree_to_jobitem(anytree_node, parent_item=None):

        node_type = anytree_node.node_type
        new_item = jobItem.JobItem(parent=parent_item)
        if node_type == 'Job':
            new_item.set_name(anytree_node.job_name)
            new_item.set_ID(anytree_node.name)
            new_item.set_status(anytree_node.status)
            new_item.set_progress(anytree_node.progress)

        if node_type == 'Allocation':
            children = anytree_node.children
            start_frame_task = children[0]
            end_frame_task = children[-1]

            new_item.set_name(f'{start_frame_task.frame}-{end_frame_task.frame}')
            new_item.set_ID(anytree_node.name)
            new_item.set_status(anytree_node.status)
            new_item.set_progress(anytree_node.progress)

        if node_type == 'Task':
            new_item.set_name(str(anytree_node.frame))
            new_item.set_ID(anytree_node.name)
            new_item.set_status(anytree_node.status)
            new_item.set_progress(anytree_node.progress)

        if node_type == 'root':
            new_item.set_name('root')
            new_item.set_ID(-1)
            new_item.set_progress(0)

        if parent_item is not None:
            parent_item.appendChild(new_item)

        for child in anytree_node.children:
            convert_anytree_to_jobitem(child, parent_item=new_item)

        return new_item

    class MainWindow(QMainWindow):
        def __init__(self, event_loop=None):
            super().__init__()
            root_item = convert_anytree_to_jobitem(job_tree.root)
            model = JobTreeModel(root_item)
            self.event_loop = event_loop
            self.tree_widget = QTreeView(self)
            self.tree_widget.setModel(model)
            self.setCentralWidget(self.tree_widget)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
