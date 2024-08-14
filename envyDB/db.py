import sqlite3, os, logging
from config import Config
from envyLib.envy_utils import DummyLogger
from envyJobs import job as j


class DB:
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or DummyLogger()
        self.connection = None
        self.cursor = None
        self.db_path = os.path.join(Config.ENVYPATH, 'Jobs', 'Envy_Database.db')

    def connect(self) -> bool:
        self.logger.debug('connecting to database')
        try:
            self.connection = sqlite3.connect(self.db_path)
        except Exception as e:
            self.logger.error(e)
            return False
        self.cursor = self.connection.cursor()
        self.logger.debug('connected to database')
        return True

    def configure_db(self):
        # todo implement startup configuration
        self.logger.info('configuring database')

    def add_job(self, job: j.Job) -> bool:
        name = str(job)
        purpose = job.get_purpose()
        job_type = job.get_type()
        metadata = job.get_meta()
        start = job.get_start()
        end = job.get_end()
        increment = job.get_increment()

        """
        plan:
            1. check if a job with that name already exists
                a. if True:
                    then append the current job information onto that job if they are the same purpose
                    probably have some sort of append_to_job method
                b. if False:
                    Then create a new job
            2. check the frame range of the job and create a row in the job table for each frame / increment
            
        """

        self.logger.info(f'Creating Job: ({name})')
        pass
