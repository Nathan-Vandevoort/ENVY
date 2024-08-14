import sqlite3, os, logging
from config import Config
from envyLib.envy_utils import DummyLogger
from envyJobs import job as j
from envyJobs.enums import Status

"""
'select id from JOBS where id=?', (identifier,) match by ID
"""


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
        self.logger.info('configuring database')
        list_of_tables = self.cursor.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND tableName='jobs';
        """).fetchall()

        if list_of_tables == []:
            self.logger.info('jobs table not found creating jobs table')
            self.cursor.execute("""
            CREATE TABLE jobs(name, id, purpose, type, metadata, range, status, environment, dependencies, parameters)
            """)

        list_of_tables = self.cursor.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND tableName='tasks';
                """).fetchall()

        if list_of_tables == []:
            self.logger.info('tasks table not found creating tasks table')
            self.cursor.execute("""
                        CREATE TABLE tasks(job_id, task_id, purpose, type, frame, status, environment, dependencies, parameters)
                        """)

    def add_job(self, job: j.Job) -> bool:
        name = str(job)
        identifier = job.get_id()
        purpose = job.get_purpose()
        job_type = job.get_type()
        metadata = job.get_meta()
        frames = job.range_as_list()
        frame_range = job.get_range()
        environment = job.get_environment()
        dependencies = job.get_dependencies()
        parameters = job.get_parameters()

        # create job
        try:
            self.logger.info(f'Creating Job: ({name})')
            self.cursor.execute(f"""
            INSERT INTO JOB VALUES
            ({name}, {identifier}, {purpose}, {job_type}, {metadata}, {frame_range}, {Status.PENDING}, {environment}, {dependencies}, {parameters})
            """)
        except Exception as e:
            self.logger.error(f'Failed to create job {job} for reason: {e}')
            return False

        data = []
        for i, frame in enumerate(frames):
            data.append(
                (identifier, i, purpose, job_type, frame, Status.PENDING, environment, dependencies, parameters))

        self.cursor.executemany(
            """
            INSERT INTO tasks VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            data
        )

        self.connection.commit()
