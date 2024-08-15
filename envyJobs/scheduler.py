import envyJobs.job as j
import logging
from envyLib.envy_utils import DummyLogger
from envyJobs.enums import Status
import asyncio
import envyJobs.ingestor as ingestor
from envyDB import db


class Scheduler:
    def __init__(self, server, event_loop, logger: logging.Logger = None):
        self.logger = logger or DummyLogger()

        self.pending_jobs = {}
        self.active_jobs = {}

        self.event_loop = event_loop
        self.ingestor = ingestor.Ingestor(logger=self.logger)
        self.job_db = db.DB(logger=self.logger)

        self.tasks = []

        self.clients = server.clients

    def sync_from_db(self) -> None:
        self.logger.debug('Scheduler: syncing from database')
        pending_jobs = self.job_db.get_jobs_by_status(Status.PENDING)
        self.logger.debug(f'Scheduler: pending_jobs -> {pending_jobs}')
        active_jobs = self.job_db.get_jobs_by_status(Status.INPROGRESS)
        self.logger.debug(f'Scheduler: active_jobs -> {active_jobs}')

        for job in pending_jobs:
            new_job = j.job_from_sqlite(job, logger=self.logger)
            job_id = new_job.get_id()
            self.pending_jobs[new_job.get_id()] = {
                job_id: new_job,
                'Pending_Tasks': list(self.job_db.get_tasks_by_status(job_id, Status.PENDING, column='Task_Id')),
                'Active_Tasks': list(self.job_db.get_tasks_by_status(job_id, Status.INPROGRESS, column='Task_Id'))
            }

        for job in active_jobs:
            new_job = j.job_from_sqlite(job, logger=self.logger)
            job_id = new_job.get_id()
            self.active_jobs[new_job.get_id()] = {
                job_id: new_job,
                'Pending_Tasks': list(self.job_db.get_tasks_by_status(job_id, Status.PENDING, column='Task_Id')),
                'Active_Tasks': list(self.job_db.get_tasks_by_status(job_id, Status.INPROGRESS, column='Task_Id'))
            }

    def task_finished(self, task_id: int) -> None:
        self.job_db.update_task_status(task_id, Status.DONE)

    def issue_task_to_client(self, task_id: int, client: str):
        self.logger.info(f'Scheduler: Issuing task ({task_id}) to {client}')
        pass

    async def start(self):
        self.job_db.connect()
        self.ingestor.set_db(self.job_db)

        ingestor_task = self.event_loop.create_task(self.ingestor.start())
        ingestor_task.set_name('ingestor.start()')
        self.tasks.append(ingestor_task)

        self.sync_from_db()

        while True:
            await asyncio.sleep(5)
            for client in self.clients:
                if client['Status'] != Status.IDLE:
                    continue




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