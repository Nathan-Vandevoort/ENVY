import sys
import prep_env
import config_bridge
from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex, Signal, Slot
from PySide6.QtWidgets import QMainWindow, QApplication, QTreeView
from envyDB import db
from envyJobs import jobTree
from envyJobs.jobItem import JobItem

class JobTreeModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super(JobTreeModel, self).__init__(parent)
        self.header = ['Job Name', 'Progress', 'Status', 'Computer']
        self.data_base = db.DB()
        self.job_tree = jobTree.JobTree()
        self.model = None
        self.configure_tree()
        self._rootItem = self.job_tree.root

    def configure_tree(self):
        self.data_base.start()
        self.job_tree.enable_read_only()
        self.job_tree.skip_complete_tasks = False
        self.job_tree.skip_complete_allocations = False
        self.job_tree.set_db(self.data_base)
        self.job_tree.build_from_db()

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

    def index_from_item(self, item: JobItem) -> QModelIndex:
        if item is None or item == self._rootItem:
            return QModelIndex()

        parent_item = item.parent
        if parent_item is None:
            return QModelIndex()

        row = parent_item.row()
        return self.createIndex(row, 0, item)

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

    def mark_job_as_finished(self, job_id: int) -> None:
        job = self.job_tree.finish_job(job_id)
        if job is None:
            return
        index = self.index_from_item(job)
        self.dataChanged.emit(index, index, [Qt.DisplayRole])

    def sync_job(self, job_id: int) -> None:
        row = self._rootItem.child_count()
        self.beginInsertRows(self.index_from_item(self._rootItem), row, row)
        job = self.job_tree.sync_job(job_id, return_new_job=True)
        if job is None:
            return
        self.endInsertRows()