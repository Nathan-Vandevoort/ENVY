import anytree.resolver
from anytree import Node, RenderTree, Resolver
import networkUtils.message
from envyDB import db
import logging
from envyLib.envy_utils import DummyLogger
from envyJobs.enums import Status as Job_Status
import json
from networkUtils.message_purpose import Message_Purpose


class JobTree:
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or DummyLogger()

        self.root = Node(name='root')
        self.db = None
        self.resolver = Resolver()
        self.number_of_jobs = 0

    def set_db(self, db):
        self.db = db

    def build_from_db(self) -> list:
        self.logger.debug('JobTree: building tree from database')
        jobs = list(self.db.get_ids_by_value('jobs', 'Status', Job_Status.INPROGRESS))
        jobs.extend(list(self.db.get_ids_by_value('jobs', 'Status', Job_Status.PENDING)))

        active_allocations = []
        for job in jobs:
            job = job[0]
            active_allocations.extend(self.sync_job(job))
        return active_allocations

    def sync_job(self, job_id: int) -> list:
        self.logger.debug(f'JobTree: syncing job: {job_id} from database to tree')

        job_values = self.db.get_job_values(job_id)
        job_name = job_values[1]
        job_purpose = job_values[3]
        job_type = job_values[5]
        job_environment = json.loads(job_values[6])
        job_parameters = json.loads(job_values[7])
        job_status = job_values[9]
        job_dependencies = job_values[10]
        job_allocation = job_values[11]

        new_job = Node(
            name=job_id,
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
            parent=self.root
        )
        print(job_id)
        allocation_ids = self.db.get_allocation_ids(job_id)
        pending_allocations = []
        active_allocations = []
        done_allocations = []
        for allocation_id in allocation_ids:
            allocation_status = self.db.get_allocation_value(allocation_id, 'Status')

            if allocation_status == Job_Status.DONE or allocation_status == Job_Status.DIRTY:
                done_allocations.append(allocation_id)
                continue

            if allocation_status == Job_Status.INPROGRESS:
                active_allocations.append(allocation_id)

            if allocation_status == Job_Status.PENDING:
                pending_allocations.append(allocation_id)

            allocation_computer = self.db.get_allocation_value(allocation_id, 'Computer')

            new_allocation = Node(
                name=allocation_id,
                pending_tasks=[],
                active_tasks=[],
                status=allocation_status,
                progress=0,
                computer=allocation_computer,
                parent=new_job
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

                if task_status == Job_Status.DONE or task_status == Job_Status.DIRTY:
                    done_tasks.append(task_id)
                    continue

                if task_status == Job_Status.INPROGRESS:
                    active_tasks.append(task_id)

                if task_status == Job_Status.PENDING:
                    pending_tasks.append(task_id)

                new_task = Node(
                    name=task_id,
                    frame=task_frame,
                    status=task_status,
                    progress=0,
                    computer=task_computer,
                    parent=new_allocation
                )
            new_allocation.pending_tasks = pending_tasks
            new_allocation.active_tasks = active_tasks

            progress = len(done_tasks) / (len(pending_tasks) + len(active_tasks) + len(done_tasks))
            progress = round(progress, 2)

            new_allocation.progress = progress

        new_job.pending_allocations = pending_allocations
        new_job.active_allocations = active_allocations

        progress = len(done_allocations) / (len(pending_allocations) + len(active_allocations) + len(done_allocations))
        progress = round(progress, 2)

        new_job.progress = progress
        self.number_of_jobs += 1
        return active_allocations

    def finish_task(self, task_id: int) -> bool:
        job_id = self.db.get_task_value(task_id, 'Job_Id')
        allocation_id = self.db.get_task_value(task_id, 'Allocation_Id')
        self.db.set_task_value(task_id, 'Status', Job_Status.DONE)
        try:
            task_node = self.resolver.get(self.root, f'/root/{job_id}/{allocation_id}/{task_id}')
        except anytree.resolver.ChildResolverError as e:
            self.logger.warning(f'Failed to finish task {task_id} - {e}')
            return False
        allocation_node = task_node.parent
        task_node.parent = None

        self.logger.info(f'JobTree: {task_node.computer} Finished task {task_id}')
        if len(allocation_node.children) == 0:
            self.finish_allocation(allocation_node)

        return True

    def finish_allocation(self, allocation: Node | int) -> None:
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
            self.logger.debug(f'JobTree: Allocation {allocation_id} is already marked as finished')
            return

        allocation_id = allocation.name
        self.db.set_allocation_value(allocation_id, 'Status', Job_Status.DONE)
        job_node = allocation.parent
        allocation.parent = None

        self.logger.debug(f'JobTree: Finished allocation {allocation_id}')
        if len(job_node.children) == 0:
            self.finish_job(job_node)

    def finish_job(self, job: int | Node) -> None:
        if isinstance(job, int):
            job = self.resolver.get(self.root, f'/root/{job}')

        job_id = job.name
        self.db.set_job_value(job_id, 'Status', Job_Status.DONE)
        job.parent = None
        self.number_of_jobs -= 1
        self.logger.debug(f'JobTree: Finished Job {job_id}')

    def reset_task(self, task: int | Node):

        if isinstance(task, int):
            task = self.get_task(task)

        task.status = Job_Status.PENDING
        task.computer = None
        task.progress = 0
        self.logger.debug(f'JobTree: Reset task {task}')
        return True

    def reset_allocation(self, allocation_id: int):
        self.logger.debug(f'resetting allocation {allocation_id}')
        job_id = self.db.get_allocation_value(allocation_id, 'Job_Id')
        self.db.set_allocation_value(allocation_id, 'Status', Job_Status.PENDING)

        try:
            allocation_node = self.resolver.get(self.root, f'/root/{job_id}/{allocation_id}')
        except anytree.resolver.ChildResolverError as e:
            self.logger.warning(f'JobTree: Failed to reset allocation {allocation_id} - {e}')
            return False

        for task_node in allocation_node.children:
            self.reset_task(task_node)

        allocation_node.status = Job_Status.PENDING
        allocation_node.computer = None
        allocation_node.progress = 0
        self.logger.debug(f'JobTree: Reset allocation {allocation_id}')
        return True

    def pick_allocation(self) -> Node | None:
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
            self.logger.debug(f'cannot find allocation {allocation_id}')
            return None
        return allocation_node

    def get_task(self, task_id: int):
        job_id = self.db.get_task_value(task_id, 'Job_Id')
        allocation_id = self.db.get_task_value(task_id, 'Allocation_Id')
        self.db.set_task_value(task_id, 'Status', Job_Status.DONE)
        try:
            task_node = self.resolver.get(self.root, f'/root/{job_id}/{allocation_id}/{task_id}')
        except anytree.resolver.ChildResolverError as e:
            self.logger.warning(f'JobTree: Failed to find task {task_id} - {e}')
            return False
        return task_node

    def start_allocation(self, computer: str, allocation: int | Node) -> None:
        if isinstance(allocation, int):
            allocation = self.get_allocation(allocation)
        self.logger.debug(f'JobTree: starting Allocation({allocation.name}) for {computer}')

        job_node = allocation.parent

        if job_node.status != Job_Status.INPROGRESS:
            job_node.status = Job_Status.INPROGRESS

        allocation.status = Job_Status.INPROGRESS
        allocation.computer = computer

        self.db.set_allocation_value(allocation.name, 'Status', Job_Status.INPROGRESS)
        self.db.set_allocation_value(allocation.name, 'Computer', computer)

    def start_task(self, task_id: int, computer: str) -> None:
        task_node = self.get_task(task_id)
        task_node.computer = computer
        task_node.status = Job_Status.INPROGRESS

        self.db.set_task_value(task_id, 'Status', Job_Status.INPROGRESS)
        self.db.set_task_value(task_id, 'Computer', computer)

    def allocation_as_message(self, allocation: Node | int) -> networkUtils.message.FunctionMessage:
        self.logger.debug("ALLOCATION AS MESSAGE")
        if isinstance(allocation, Node):
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

        new_message = networkUtils.message.FunctionMessage(f'Job: {name} Allocation: {allocation}')
        new_message.set_function(job_type)
        new_message.format_arguments(json.dumps(data))
        new_message.set_target(Message_Purpose.CLIENT)
        self.logger.debug(f'DB: Wrote Allocation: {allocation} as message')
        return new_message

    def print_tree(self):
        print(RenderTree(self.root))

if __name__ == '__main__':
    class CustomFormatter(logging.Formatter):
        # Define color codes
        grey = "\x1b[38;20m"
        yellow = "\x1b[33;20m"
        red = "\x1b[31;20m"
        bold_red = "\x1b[31;1m"
        reset = "\x1b[0m"

        # Define format
        format = '%(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'

        FORMATS = {
            logging.DEBUG: grey + format + reset,
            logging.INFO: yellow + format + reset,
            logging.WARNING: yellow + format + reset,
            logging.ERROR: red + format + reset,
            logging.CRITICAL: bold_red + format + reset
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)


    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    db = db.DB(logger=logger)
    db.start()

    tree = JobTree(logger=logger)
    tree.set_db(db)
    tree.build_from_db()

    target_allocation = tree.get_allocation(4)
    tree.print_tree()
