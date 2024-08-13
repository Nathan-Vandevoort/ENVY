import os, json, asyncio
from job import Job
import logging
from envyLib.envy_utils import DummyLogger


class Ingester:
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or DummyLogger()
        self.running = False
        self.path = None
        self.db = None

    def set_path(self, path: str):
        self.logger.debug(f'Set path -> {path}')
        self.path = path

    def set_db(self, db):
        self.logger.debug(f'Set Database -> {db}')
        self.db = db

    async def start(self):
        self.logger.debug('Started envyJobs.ingester.Ingester')
        self.running = True
        while self.running:
            await asyncio.sleep(2)  # let other coroutines run

            new_jobs = await self.check_for_new_jobs()  # check for new jobs

            if len(new_jobs) == 0:  # if there are no new jobs then continue on
                continue

            self.logger.info(f'New jobs found {new_jobs}')
            for job in new_jobs:
                success = await self.ingest(job)

    async def ingest(self, job_path: str) -> bool:
        file, ext = os.path.splitext(job_path)
        job_path = os.path.join(self.path, job_path)

        if ext.upper() != '.JSON':
            self.logger.warning(f'{job_path} is not a valid job file (not a .json file)')
            return False

        with open(job_path, 'r') as job_file:
            job_as_dict = json.load(job_file)
            job_file.close()


    async def check_for_new_jobs(self) -> list:
        new_jobs = os.listdir(self.path)
        return new_jobs
