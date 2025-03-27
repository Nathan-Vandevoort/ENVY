import asyncio
import json
import logging
import os

import envy
import envy.lib.jobs.job as job

logger = logging.getLogger(__name__)


class Ingestor:
    def __init__(self, scheduler):
        self.running = False
        self.path = os.path.join(envy.__file__, 'Jobs', 'Jobs')
        self.db = None
        self.scheduler = scheduler

    def set_db(self, db):
        logger.debug(f'Set Database -> {db}')
        self.db = db

    async def add_to_db(self, job_to_add: job.Job) -> int:
        logger.debug(f'adding {job_to_add} to database')
        new_job_id = self.db.add_job(job_to_add)
        if new_job_id is None:
            raise Exception('Failed to create job database may be corrupted now')
        return new_job_id

    async def start(self):
        logger.debug('Started jobs.ingester.Ingestor')
        self.running = True
        while self.running:
            await asyncio.sleep(2)  # let other coroutines run

            new_jobs = await self.check_for_new_jobs()  # check for new jobs

            if len(new_jobs) == 0:  # if there are no new jobs then continue on
                continue

            logger.info(f'New jobs found {new_jobs}')
            for envy_job in new_jobs:
                try:
                    await self.ingest(envy_job)
                    os.remove(os.path.join(self.path, envy_job))
                except Exception as e:
                    logger.error(f'ingester: Failed to ingest job -> {e}')

    async def ingest(self, job_path: str):
        file, ext = os.path.splitext(job_path)
        job_path = os.path.join(self.path, job_path)
        logger.debug(f'ingester: Ingesting Job -> {file}')

        if ext.upper() != '.JSON':
            logger.warning(f'{job_path} is not a valid job file (not a .json file)')
            return False

        with open(job_path, 'r') as job_file:
            job_as_dict = json.load(job_file)
            job_file.close()
        logger.debug(f'ingester: Loaded json')

        new_job = job.job_from_dict(job_as_dict, logger=logger)
        logger.debug(f'ingester: Job Data -> {new_job}')

        new_id = await self.add_to_db(new_job)
        await self.scheduler.sync_job(new_id)

    async def check_for_new_jobs(self) -> list:
        new_jobs = os.listdir(self.path)
        return new_jobs
