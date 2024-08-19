import os, json, asyncio
import envyJobs.job as job
import logging
from envyLib.envy_utils import DummyLogger
from global_config import Config


class Ingestor:
    def __init__(self, scheduler, logger: logging.Logger = None):
        self.logger = logger or DummyLogger()
        self.running = False
        self.path = os.path.join(Config.ENVYPATH, 'Jobs', 'Jobs')
        self.db = None
        self.scheduler = scheduler

    def set_db(self, db):
        self.logger.debug(f'Set Database -> {db}')
        self.db = db

    async def add_to_db(self, job_to_add: job.Job):
        self.logger.debug(f'adding {job_to_add} to database')
        self.db.add_job(job_to_add)

    async def start(self):
        self.logger.debug('Started envyJobs.ingester.Ingestor')
        self.running = True
        while self.running:
            await asyncio.sleep(2)  # let other coroutines run

            new_jobs = await self.check_for_new_jobs()  # check for new jobs

            if len(new_jobs) == 0:  # if there are no new jobs then continue on
                continue

            self.logger.info(f'New jobs found {new_jobs}')
            for job in new_jobs:
                await self.ingest(job)
                os.remove(os.path.join(self.path, job))

    async def ingest(self, job_path: str) -> bool:
        file, ext = os.path.splitext(job_path)
        job_path = os.path.join(self.path, job_path)

        if ext.upper() != '.JSON':
            self.logger.warning(f'{job_path} is not a valid job file (not a .json file)')
            return False

        job_as_dict = None
        with open(job_path, 'r') as job_file:
            job_as_dict = json.load(job_file)
            job_file.close()

        new_job = job.job_from_dict(job_as_dict, logger=self.logger)

        await self.add_to_db(new_job)
        await self.scheduler.add_job(new_job)

    async def check_for_new_jobs(self) -> list:
        new_jobs = os.listdir(self.path)
        return new_jobs

if __name__ == '__main__':
    from envyDB import db

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    loop = asyncio.new_event_loop()

    ingester = Ingestor(logger=logger)
    my_db = db.DB(logger=logger)
    my_db.start()
    ingester.set_db(my_db)
    loop.create_task(ingester.start())
    loop.run_forever()