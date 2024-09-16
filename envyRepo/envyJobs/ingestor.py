import os, json, asyncio
import envyRepo.envyJobs.job as job
import logging
from envyRepo.envyLib.envy_utils import DummyLogger
ENVYPATH = os.environ['ENVYPATH']


class Ingestor:
    def __init__(self, scheduler, logger: logging.Logger = None):
        self.logger = logger or DummyLogger()
        self.running = False
        self.path = os.path.join(ENVYPATH, 'Jobs', 'Jobs')
        self.db = None
        self.scheduler = scheduler

    def set_db(self, db):
        self.logger.debug(f'Set Database -> {db}')
        self.db = db

    async def add_to_db(self, job_to_add: job.Job) -> int:
        self.logger.debug(f'adding {job_to_add} to database')
        new_job_id = self.db.add_job(job_to_add)
        if new_job_id is None:
            raise Exception('Failed to create job database may be corrupted now')
        return new_job_id

    async def start(self):
        self.logger.debug('Started envyJobs.ingester.Ingestor')
        self.running = True
        while self.running:
            await asyncio.sleep(2)  # let other coroutines run

            new_jobs = await self.check_for_new_jobs()  # check for new jobs

            if len(new_jobs) == 0:  # if there are no new jobs then continue on
                continue

            self.logger.info(f'New jobs found {new_jobs}')
            for envy_job in new_jobs:
                try:
                    await self.ingest(envy_job)
                    os.remove(os.path.join(self.path, envy_job))
                except Exception as e:
                    self.logger.error(f'ingester: Failed to ingest job -> {e}')

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

        new_id = await self.add_to_db(new_job)
        await self.scheduler.sync_job(new_id)

    async def check_for_new_jobs(self) -> list:
        new_jobs = os.listdir(self.path)
        return new_jobs

if __name__ == '__main__':
    from envyDB import db

    class scheduler:
        def sync_job(self):
            pass

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    loop = asyncio.new_event_loop()

    ingester = Ingestor(scheduler, logger=logger)
    my_db = db.DB(logger=logger)
    my_db.start()
    ingester.set_db(my_db)
    loop.create_task(ingester.start())
    loop.run_forever()