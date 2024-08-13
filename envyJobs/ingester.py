import os, json, asyncio
from job import Job


class Ingester:
    def __init__(self):
        self.running = False
        self.path = None
        self.db = None

    def set_path(self, path: str):
        self.path = path

    def set_db(self, db):
        self.db = db

    async def start(self):
        self.running = True
        while self.running:
            await asyncio.sleep(2)  # let other coroutines run

            new_jobs = await self.check_for_new_jobs()  # check for new jobs

            if len(new_jobs) == 0:  # if there are no new jobs then continue on
                continue

    async def check_for_new_jobs(self) -> list:
        new_jobs = os.listdir(self.path)
        return new_jobs
