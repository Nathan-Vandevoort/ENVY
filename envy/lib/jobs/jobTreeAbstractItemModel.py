import json
import logging

import anytree.resolver
from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex
from anytree import Resolver

import envy.lib.network.message
from envy.lib.jobs import jobItem
from envy.lib.jobs.enums import Status as Job_Status
from envy.lib.network.message import MessageTarget

logger = logging.getLogger(__name__)


class JobTreeItemModel(QAbstractItemModel):
    # TODO: refactor the hell out of this
    def __init__(self, parent=None):
        super(JobTreeItemModel, self).__init__(parent=parent)
        self.root = jobItem.JobItem(name='root', node_type='root', label='root')
        self.db = None
        self.resolver = Resolver()
        self.number_of_jobs = 0
        self.read_only = False
        self.skip_complete_allocations = True
        self.skip_complete_tasks = True

        #  UI Stuff
        self.header = ['Job Name', 'Progress', 'Status', 'Computer', 'Info']

    def set_db(self, db):
        self.db = db

    def enable_read_only(self):
        self.read_only = True

    def disable_read_only(self):
        self.read_only = False

    def build_from_db(self) -> list:
        logger.debug('JobTree: building tree from database')
        jobs = list(self.db.get_ids_by_value('jobs', 'Status', Job_Status.INPROGRESS))
        jobs.extend(list(self.db.get_ids_by_value('jobs', 'Status', Job_Status.PENDING)))

        active_allocations = []
        for job in jobs:
            job = job[0]
            active_allocations.extend(
                self.sync_job(
                    job,
                    skip_complete_allocations=self.skip_complete_allocations,
                    skip_complete_tasks=self.skip_complete_tasks,
                )
            )
        return active_allocations

    def sync_job(
        self,
        job_id: int,
        skip_complete_allocations: bool = True,
        skip_complete_tasks: bool = True,
        return_new_job=False,
    ) -> (list, jobItem.JobItem):
        logger.debug(f'JobTree: syncing job: {job_id} from database to tree')

        row = self.root.child_count()
        self.beginInsertRows(self.index_from_item(self.root), row, row)

        job_values = self.db.get_job_values(job_id)
        job_name = job_values[1]
        job_purpose = job_values[3]
        job_type = job_values[5]
        job_environment = json.loads(job_values[6])
        job_parameters = json.loads(job_values[7])
        job_status = job_values[9]
        job_dependencies = job_values[10]
        job_allocation = job_values[11]
        info = job_values[12]

        new_job = jobItem.JobItem(
            name=job_id,
            label=f'{job_name}',
            job_name=job_name,
            purpose=job_purpose,
            job_type=job_type,
            environment=job_environment,
            parameters=job_parameters,
            dependencies=job_dependencies,
            allocation=job_allocation,
            pending_allocations=[],
            active_allocations=[],
            status=job_status,
            progress=0,
            node_type='Job',
            parent=self.root,
            info=info,
        )
        allocation_ids = self.db.get_allocation_ids(job_id)
        pending_allocations = []
        active_allocations = []
        done_allocations = []
        for allocation_id in allocation_ids:
            allocation_status = self.db.get_allocation_value(allocation_id, 'Status')

            if (allocation_status == Job_Status.DONE or allocation_status == Job_Status.FAILED) and skip_complete_allocations is True:
                done_allocations.append(allocation_id)
                continue

            if allocation_status == Job_Status.INPROGRESS:
                active_allocations.append(allocation_id)

            if allocation_status == Job_Status.PENDING:
                pending_allocations.append(allocation_id)

            allocation_computer = self.db.get_allocation_value(allocation_id, 'Computer')
            info = self.db.get_allocation_value(allocation_id, 'Info')

            new_allocation = jobItem.JobItem(
                name=allocation_id,
                label=str(allocation_id),
                pending_tasks=[],
                active_tasks=[],
                status=allocation_status,
                progress=0,
                computer=allocation_computer,
                node_type='Allocation',
                parent=new_job,
                info=info,
            )

            task_ids = self.db.get_task_ids(allocation_id)

            pending_tasks = []
            active_tasks = []
            done_tasks = []
            for task_id in task_ids:
                task_data = self.db.get_task_values(task_id)
                task_frame = task_data[3]
                task_status = task_data[4]
                task_computer = task_data[5]

                if (task_status == Job_Status.DONE or task_status == Job_Status.FAILED) and skip_complete_tasks is True:
                    done_tasks.append(task_id)
                    continue

                if task_status == Job_Status.INPROGRESS:
                    active_tasks.append(task_id)

                if task_status == Job_Status.PENDING:
                    pending_tasks.append(task_id)

                new_task = jobItem.JobItem(
                    name=task_id,
                    label=f'Frame: {task_frame}',
                    frame=task_frame,
                    status=task_status,
                    progress='N/A',
                    computer=task_computer,
                    node_type='Task',
                    parent=new_allocation,
                )
            new_allocation.pending_tasks = pending_tasks
            new_allocation.active_tasks = active_tasks
            try:
                progress = len(done_tasks) / (len(pending_tasks) + len(active_tasks) + len(done_tasks))
            except ZeroDivisionError:
                progress = 0
            progress = round(progress, 2)
            new_allocation.progress = progress

            if len(new_allocation.children) < 1:
                done_allocations.append(allocation_id)
                new_allocation.parent = None
                continue
            else:
                new_allocation.label = f'Range: {new_allocation.children[0].frame}-{new_allocation.children[-1].frame}'

        new_job.pending_allocations = pending_allocations
        new_job.active_allocations = active_allocations

        try:
            progress = len(done_allocations) / (len(pending_allocations) + len(active_allocations) + len(done_allocations))
        except ZeroDivisionError:
            progress = 0
        progress = round(progress, 2)

        new_job.progress = progress
        self.number_of_jobs += 1
        self.endInsertRows()
        logger.debug(f'JobTree: Finished syncing job {job_id}')

        if return_new_job is True:
            return new_job

        return active_allocations

    @staticmethod
    def check_if_children_are_done(node: jobItem.JobItem) -> bool:
        for child in node.children:
            if child.status != Job_Status.DONE:
                return False
        return True

    def finish_task(self, task_id: int) -> (jobItem.JobItem, None):

        job_id = self.db.get_task_value(task_id, 'Job_Id')
        allocation_id = self.db.get_task_value(task_id, 'Allocation_Id')
        try:
            task_node = self.resolver.get(self.root, f'/root/{job_id}/{allocation_id}/{task_id}')
        except anytree.resolver.ChildResolverError as e:
            logger.warning(f'Failed to finish task {task_id} - {e}')
            return None

        allocation_node = task_node.parent
        task_node.status = Job_Status.DONE
        task_node.progress = 100
        if self.read_only is False:
            self.db.set_task_value(task_id, 'Status', Job_Status.DONE)
            task_node.parent = None

        logger.info(f'JobTree: {task_node.computer} Finished task {task_id}')
        if self.check_if_children_are_done(allocation_node) is True:
            self.finish_allocation(allocation_node)

        index = self.index_from_item(task_node, column=2)
        self.dataChanged.emit(index, [Qt.DisplayRole])

        return task_node

    def fail_task(self, task_id: int, reason: str) -> None:
        task_node = task_id
        if isinstance(task_id, int):
            task_node = self.get_task(task_id)
            if task_node is None:
                return
        if self.read_only is False:
            self.db.set_task_value(task_id, 'Status', Job_Status.FAILED)
            task_node.parent = None

        allocation_node = task_node.parent
        task_node.status = Job_Status.FAILED
        task_node.info = reason
        self.fail_allocation(allocation_node, reason)
        logger.info(f'JobTree: {task_node.computer} Failed to finish task {task_id} for reason {reason}')
        index = self.index_from_item(task_node, column=2)
        self.dataChanged.emit(index, [Qt.DisplayRole])

        return task_node

    def fail_allocation(self, allocation_id: any, reason: str) -> None:
        logger.info(f'jobTree: Failing allocation {allocation_id} for reason {reason}')
        allocation_node = allocation_id
        if isinstance(allocation_node, int):
            allocation_node = self.get_allocation(allocation_id)
            if allocation_node is None:
                return

        job_node = allocation_node.parent
        job_node.info = 'Possible Error: one or more ranges have failed'

        if self.read_only is False:
            self.db.set_allocation_value(allocation_id, 'Info', reason)
            self.db.set_allocation_value(allocation_id, 'Status', Job_Status.FAILED)
            self.db.set_job_value(job_node.name, 'Info', 'Possible Error: one or more ranges have failed')
            allocation_node.parent = None

        allocation_node.status = Job_Status.FAILED
        allocation_node.info = reason

        logger.info(f'JobTree: {allocation_node.computer} Failed to finish allocation {allocation_id} for reason {reason}')
        index = self.index_from_item(allocation_node, column=2)
        self.dataChanged.emit(index, [Qt.DisplayRole])
        index = self.index_from_item(allocation_node.parent, column=4)
        self.dataChanged.emit(index, [Qt.DisplayRole])

        return allocation_node

    def finish_allocation(self, allocation: jobItem.JobItem | int) -> (jobItem.JobItem, None):
        """
        Marks the current allocation as done in the database and removes it from the tree
        you must provide either an allocation ID or allocation node
        :param allocation: either the ID of the allocation or a reference to the allocation node
        :return:
        """
        allocation_id = allocation
        if isinstance(allocation, int):
            allocation = self.get_allocation(allocation)

        if allocation is None:
            logger.debug(f'JobTree: Allocation {allocation_id} is already marked as finished')
            return

        job_node = allocation.parent
        allocation_id = allocation.name
        allocation.status = Job_Status.DONE
        allocation.progress = 100
        if self.read_only is False:
            self.db.set_allocation_value(allocation_id, 'Status', Job_Status.DONE)
            allocation.parent = None

        logger.debug(f'JobTree: Finished allocation {allocation_id}')
        if self.check_if_children_are_done(job_node) is True:
            self.finish_job(job_node)

        index = self.index_from_item(allocation, column=2)
        self.dataChanged.emit(index, [Qt.DisplayRole])

        return allocation

    def finish_job(self, job: int | jobItem.JobItem) -> (jobItem.JobItem, None):
        if isinstance(job, int):
            try:
                job = self.resolver.get(self.root, f'/root/{job}')
            except anytree.resolver.ChildResolverError:
                logger.debug(f'JobTree: Job {job} is already marked as finished')
                return None
        job_id = job.name
        job.status = Job_Status.DONE
        job.progress = 100
        if self.read_only is False:
            self.db.set_job_value(job_id, 'Status', Job_Status.DONE)
            job.parent = None
        self.number_of_jobs -= 1
        logger.debug(f'JobTree: Finished Job {job_id}')

        index = self.index_from_item(job, column=2)
        self.dataChanged.emit(index, [Qt.DisplayRole])

        return job

    def reset_task(self, task: int | jobItem.JobItem):
        if isinstance(task, int):
            task = self.get_task(task)
        task.status = Job_Status.PENDING
        task.computer = None
        task.progress = 0
        logger.debug(f'JobTree: Reset task {task}')

        index = self.index_from_item(task, column=2)
        self.dataChanged.emit(index, [Qt.DisplayRole])

        return True

    def reset_allocation(self, allocation_id: int):
        logger.debug(f'resetting allocation {allocation_id}')
        job_id = self.db.get_allocation_value(allocation_id, 'Job_Id')

        if self.read_only is False:
            self.db.set_allocation_value(allocation_id, 'Status', Job_Status.PENDING)

        try:
            allocation_node = self.resolver.get(self.root, f'/root/{job_id}/{allocation_id}')
        except anytree.resolver.ChildResolverError as e:
            logger.warning(f'JobTree: Failed to reset allocation {allocation_id} - {e}')
            return False

        for task_node in allocation_node.children:
            self.reset_task(task_node)

        allocation_node.status = Job_Status.PENDING
        allocation_node.computer = None
        allocation_node.progress = 0
        logger.debug(f'JobTree: Reset allocation {allocation_id}')
        return True

    def pick_allocation(self) -> jobItem.JobItem | None:
        if len(self.root.children) == 0:
            yield None
        for job in self.root.children:
            for allocation in job.children:
                yield allocation
        yield None

    def get_allocation(self, allocation_id: int):
        job_id = self.db.get_allocation_value(allocation_id, 'Job_Id')
        try:
            allocation_node = self.resolver.get(self.root, f'/root/{job_id}/{allocation_id}')
        except anytree.resolver.ChildResolverError as e:
            logger.debug(f'cannot find allocation {allocation_id}')
            return None
        return allocation_node

    def get_task(self, task_id: int):
        job_id = self.db.get_task_value(task_id, 'Job_Id')
        allocation_id = self.db.get_task_value(task_id, 'Allocation_Id')
        self.db.set_task_value(task_id, 'Status', Job_Status.DONE)
        try:
            task_node = self.resolver.get(self.root, f'/root/{job_id}/{allocation_id}/{task_id}')
        except anytree.resolver.ChildResolverError as e:
            logger.warning(f'JobTree: Failed to find task {task_id} - {e}')
            return None
        return task_node

    def start_allocation(self, computer: str, allocation: int | jobItem.JobItem) -> (jobItem.JobItem, None):
        if isinstance(allocation, int):
            allocation = self.get_allocation(allocation)
        logger.debug(f'JobTree: starting Allocation({allocation.name}) for {computer}')

        if allocation is None:
            return

        job_node = allocation.parent

        if job_node.status != Job_Status.INPROGRESS:
            job_node.status = Job_Status.INPROGRESS

        allocation.status = Job_Status.INPROGRESS
        allocation.computer = computer

        if self.read_only is False:
            self.db.set_allocation_value(allocation.name, 'Status', Job_Status.INPROGRESS)
            self.db.set_allocation_value(allocation.name, 'Computer', computer)

        index = self.index_from_item(allocation, column=2)
        self.dataChanged.emit(index, [Qt.DisplayRole])

        return allocation

    def start_task(self, task_id: int, computer: str) -> (jobItem.JobItem, None):
        task_node = self.get_task(task_id)

        if task_node is None:
            return

        task_node.computer = computer
        task_node.status = Job_Status.INPROGRESS

        if self.read_only is False:
            self.db.set_task_value(task_id, 'Status', Job_Status.INPROGRESS)
            self.db.set_task_value(task_id, 'Computer', computer)

        index = self.index_from_item(task_node, column=2)
        self.dataChanged.emit(index, [Qt.DisplayRole])

        return task_node

    def allocation_as_message(self, allocation: jobItem.JobItem | int) -> envy.lib.network.message.FunctionMessage:
        if isinstance(allocation, jobItem.JobItem):
            allocation = allocation.name
        allocation_id = allocation
        allocation = self.db.get_allocation_values(allocation)
        job_id = allocation[1]
        task_ids = json.loads(allocation[2])

        job_values = self.db.get_job_values(job_id)
        name = job_values[1]
        purpose = job_values[3]
        job_type = job_values[5]
        environment = job_values[6]
        environment = json.loads(environment)
        parameters = job_values[7]
        parameters = json.loads(parameters)

        tasks = {}
        for task in task_ids:
            task = int(task)
            task_status = self.db.get_task_value(task, 'Status')
            frame = self.db.get_task_value(task, 'Frame')

            # skip if the task is done
            if task_status == Job_Status.DONE:
                continue

            tasks[task] = frame

        data = {
            'Allocation_Id': allocation_id,
            'Purpose': purpose,
            'Tasks': tasks,
            'Environment': environment,
            'Parameters': parameters,
        }

        new_message = envy.envyRepo.networkUtils.message.FunctionMessage(f'Job: {name} Allocation: {allocation_id}')
        new_message.set_function(job_type)
        new_message.format_arguments(json.dumps(data))
        new_message.set_target(MessageTarget.CLIENT)
        logger.debug(f'DB: Wrote Allocation: {allocation} as message')
        return new_message

    def update_allocation_progress(self, allocation_id: int, progress: int):
        allocation_node = allocation_id
        if isinstance(allocation_node, int):
            allocation_node = self.get_allocation(allocation_id)

        if allocation_node is None:
            return

        job_node = allocation_node.parent

        allocation_node.progress = int(progress)
        self.update_job_progress(job_node)
        index = self.index_from_item(allocation_node, column=1)
        self.dataChanged.emit(index, [Qt.DisplayRole])

    def update_job_progress(self, job_id: int):
        job_node = job_id
        if isinstance(job_node, int):
            try:
                job_node = self.resolver.get(self.root, f'/root/{job_node}')
            except anytree.resolver.ChildResolverError:
                logger.info(f'jobTree: unable to find job {job_node}')
                return

        progresses = 0
        counter = 0
        for allocation in job_node.children:
            progresses += allocation.progress
            counter += 1
        job_node.progress = int(progresses / counter)
        index = self.index_from_item(job_node, column=1)
        self.dataChanged.emit(index, [Qt.DisplayRole])

    # ----------------------------------------- QAbstractItemModel overrides -------------------------------------

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return self.root.child_count()
        return parent.internalPointer().child_count()

    def columnCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return self.root.columnCount()
        return parent.internalPointer().columnCount()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = self.getItem(index)
        parentItem = childItem.parent
        if not parentItem or parentItem == self.root:
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

    def index_from_item(self, item: jobItem.JobItem, column=0) -> QModelIndex:
        if item is None or item == self.root:
            return QModelIndex()

        parent_item = item.parent
        if parent_item is None:
            return QModelIndex()

        row = parent_item.row()
        return self.createIndex(row, column, item)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[section]
        return None

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        if role != Qt.EditRole or orientation != Qt.Horizontal:
            return False

        result = self.root.set_data(section, value)
        return result

    def getItem(self, index) -> jobItem.JobItem:
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.root

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or (role != Qt.DisplayRole and role != Qt.EditRole):
            return None
        item = self.getItem(index)
        return item.data(index.column())
