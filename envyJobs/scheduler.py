import envyJobs.job as j
import logging
from envyLib.envy_utils import DummyLogger
from envyJobs.enums import Status
import asyncio
import envyJobs.ingestor as ingestor
from envyDB import db
import sys
SRV = sys.modules.get('Server_Functions')


class Scheduler:
    def __init__(self, server, event_loop, logger: logging.Logger = None):
        self.server = server
        self.logger = logger or DummyLogger()

        self.jobs = {}
        self.task_order = []
        self.tasks = {}

        self.event_loop = event_loop
        self.ingestor = ingestor.Ingestor(self, logger=self.logger)
        self.job_db = db.DB(logger=self.logger)

        self.scheduler_tasks = []

        self.clients = server.clients

    async def sync_from_db(self) -> None:
        self.logger.debug('Scheduler: syncing from database')
        jobs = list(self.job_db.get_jobs_by_status(Status.INPROGRESS))
        jobs.extend(list(self.job_db.get_jobs_by_status(Status.PENDING)))

        for job in jobs:
            new_job = j.job_from_sqlite(job, logger=self.logger)
            job_id = new_job.get_id()
            self.jobs[job_id] = {
                'Pending_Tasks': list(self.job_db.get_tasks_by_status(job_id, Status.PENDING, column='Task_Id')),
                'Active_Tasks': list(self.job_db.get_tasks_by_status(job_id, Status.INPROGRESS, column='Task_Id'))
            }
            for i, task in enumerate(self.jobs[job_id]['Active_Tasks']):
                computer = self.job_db.get_value_from_task_id(task, column='Computer')[0]
                if computer not in self.clients:
                    self.jobs[job_id]['Active_Tasks'].pop(i)
                    self.jobs[job_id]['Pending_Tasks'].append(task)
                    continue
                self.tasks[task] = {
                    'Status': Status.INPROGRESS,
                    'Progress': 0,
                    'Computer': computer
                }
                self.task_order.append(task)

            for task in self.jobs[job_id]['Pending_Tasks']:
                self.tasks[task] = {
                    'Status': Status.PENDING,
                    'Progress': 0,
                    'Computer': None
                }
                self.task_order.append(task)

    async def add_job(self, job: j.Job):
        self.logger.info(f'Scheduler: Adding in memory job {job}')
        job_id = job.get_id()
        self.jobs[job_id] = {
            'Pending_Tasks': list(self.job_db.get_tasks_by_status(job_id, Status.PENDING, column='Task_Id')),
            'Active_Tasks': list(self.job_db.get_tasks_by_status(job_id, Status.INPROGRESS, column='Task_Id'))
        }
        for i, task in enumerate(self.jobs[job_id]['Active_Tasks']):
            computer = self.job_db.get_value_from_task_id(task, column='Computer')[0]
            if computer not in self.clients:
                self.jobs[job_id]['Active_Tasks'].pop(i)
                self.jobs[job_id]['Pending_Tasks'].append(task)
                continue
            self.tasks[task] = {
                'Status': Status.INPROGRESS,
                'Progress': 0,
                'Computer': computer
            }
            self.task_order.append(task)

        for task in self.jobs[job_id]['Pending_Tasks']:
            self.tasks[task] = {
                'Status': Status.PENDING,
                'Progress': 0,
                'Computer': None
            }
            self.task_order.append(task)

    async def issue_task(self, task_id: int, computer_name: str) -> None:
        self.logger.info(f'Scheduler: issuing task ({task_id}) to {computer_name}')
        job_id = self.job_db.get_value_from_task_id(task_id, column='Job_Id')[0]

        self.job_db.set_task_value(task_id, Status.INPROGRESS, column='Status')  # mark the task as INPROGRESS in the database
        try:  # if task is in pending tasks move it to active tasks
            task_index = self.jobs[job_id]['Pending_Tasks'].index(task_id)
            new_task = self.jobs[job_id]['Pending_Tasks'].pop(task_index)
            self.jobs[job_id]['Active_Tasks'].append(new_task)
            self.logger.debug(f'Scheduler: Moved Task in job {job_id} from Pending to Active')
        except ValueError:  # if task is already in active tasks do nothing
            self.logger.info(f'Scheduler: Task {task_id} is already active')

        self.job_db.set_task_value(task_id, computer_name, column='Computer')  # say which computer is doing the task in db
        self.clients[computer_name]['Job'] = job_id
        self.clients[computer_name]['Task'] = task_id

        self.tasks[task_id]['Status'] = Status.INPROGRESS
        self.tasks[task_id]['Computer'] = computer_name

        await SRV.send_to_client(self.server, computer_name, self.job_db.get_task_as_message(task_id))

    def finish_job(self, job_id):
        self.job_db.set_job_value(job_id, Status.DONE, column='Status')
        del self.jobs[job_id]
        self.logger.info(f'Scheduler: Marking job: {job_id} as Done')

    def finish_task(self, task_id: int) -> None:
        task_id = int(task_id)
        job_id = self.job_db.get_value_from_task_id(task_id, column='Job_Id')[0]
        self.job_db.set_task_value(task_id, Status.DONE, column='Status')  # mark the task as DONE in the database

        task_index = self.jobs[job_id]['Active_Tasks'].index(task_id)
        self.jobs[job_id]['Active_Tasks'].pop(task_index)  # remove task from jobs list of active tasks

        task_index = self.task_order.index(task_id)  # remove task from task_order list
        self.task_order.pop(task_index)

        computer = self.tasks[task_id]['Computer']
        self.clients[computer]['Job'] = None
        self.clients[computer]['Task'] = None
        self.clients[computer]['Progress'] = 0
        del self.tasks[task_id]

        if len(self.jobs[job_id]["Pending_Tasks"]) == 0 and len(self.jobs[job_id]["Active_Tasks"]) == 0:
            self.finish_job(job_id)
        self.logger.info(f'Scheduler: Finished task {task_id}')

    def reorder_tasks(self, task_id: int, new_index: int) -> bool:
        try:
            found_index = self.task_order.index(task_id)
        except ValueError as e:
            self.logger.error(f'Scheduler: {e}')
            return False

        if new_index > len(self.task_order):
            self.logger.error(f'Scheduler: Cannot move job outside bounds of job_order list')
            return False

        self.logger.info(f'Scheduler: moving job from index: {found_index} -> {new_index}')

        if new_index <= found_index:
            self.task_order.insert(new_index, task_id)
            self.task_order.pop(found_index + 1)
            return True

        else:
            self.task_order.insert(new_index, task_id)
            self.task_order.pop(found_index)
            return True

    def pick_task(self, computer: str) -> int:
        for task in self.task_order:
            if self.tasks[task]['Computer'] is not None:
                continue
            return task

    async def start(self):
        self.logger.debug("Scheduler: Started")
        self.job_db.start()
        self.ingestor.set_db(self.job_db)

        ingestor_task = self.event_loop.create_task(self.ingestor.start())
        ingestor_task.set_name('ingestor.start()')
        self.scheduler_tasks.append(ingestor_task)

        await self.sync_from_db()

        while True:
            await asyncio.sleep(2)
            if len(self.task_order) == 0:
                continue

            for client in self.clients:
                if self.clients[client]['Status'] != Status.IDLE:
                    continue

                task = self.pick_task(client)
                if task is not None:
                    await self.issue_task(task, client)


if __name__ == '__main__':
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    loop = asyncio.new_event_loop()
    sched = Scheduler(loop, logger=logger)
    sched.start()
    loop.run_forever()
