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
        self.connection.execute("PRAGMA foreign_keys = 1")
        self.cursor = self.connection.cursor()
        self.logger.debug('connected to database')
        return True

    def configure_db(self):
        self.logger.info('configuring database')

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs
        (Job_Id INTEGER PRIMARY KEY,
        Name TEXT NOT NULL,  
        purpose TEXT, 
        type TEXT, 
        metadata TEXT, 
        range TEXT, 
        status TEXT, 
        environment TEXT, 
        dependencies TEXT, 
        parameters TEXT)
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks
        (Job_Id INTEGER,
        Task_Id INTEGER PRIMARY KEY, 
        Purpose TEXT, 
        Type TEXT, 
        Frame INTEGER, 
        Status TEXT, 
        Environment TEXT, 
        Dependencies TEXT, 
        Parameters TEXT,
        Computer TEXT,
        FOREIGN KEY(Job_Id) REFERENCES jobs(Job_Id))
        """)

    def start(self):
        self.connect()
        self.configure_db()

    def remove_job(self, job_id: int, ensure_done: bool = True) -> bool:

        if ensure_done:
            query = """
            SELECT Status
            FROM jobs
            WHERE Job_Id = ?
            """
            self.cursor.execute(query, (job_id,))
            status = self.cursor.fetchone()
            if status != Status.DONE:
                self.logger.warning(f'Job with id: {job_id} is not done, ignoring remove_job')
                return False

        query = """
        DELETE FROM tasks
        WHERE Job_Id = ?
        """
        self.cursor.execute(query, job_id)
        self.connection.commit()
        return True

    def get_tasks_from_job_id(self, job_id: int, column: str = '*') -> list:
        query = f"""
        SELECT {column}
        FROM tasks
        WHERE Job_Id = ?
        """
        self.cursor.execute(query, (job_id, ))
        tasks = self.cursor.fetchall()
        tasks = [task[0] for task in tasks]
        return tasks

    def get_tasks_by_status(self, job_id: int, status: Status, column: str = '*') -> list:
        query = f"""
        SELECT {column}
        FROM tasks
        WHERE Job_Id = ? AND Status = ?
        """
        self.cursor.execute(query, (job_id, status))
        tasks = self.cursor.fetchall()
        tasks = [task[0] for task in tasks]
        return tasks

    def update_task_status(self, task_id: int, status: Status):
        query = """
        UPDATE tasks
        SET Status = ?
        WHERE Task_Id = ?
        """
        self.cursor.execute(query, (status, task_id))
        self.connection.commit()

    def add_job(self, job: j.Job) -> bool:
        sqlite_job = job.as_sqlite_compliant()
        name = sqlite_job['Name']
        identifier = sqlite_job['ID']
        purpose = sqlite_job['Purpose']
        job_type = sqlite_job['Type']
        metadata = sqlite_job['Metadata']
        frames = job.range_as_list()
        frame_range = sqlite_job['Range']
        environment = sqlite_job['Environment']
        dependencies = sqlite_job['Dependencies']
        parameters = sqlite_job['Parameters']

        # create job
        try:
            self.logger.info(f'Creating Job: ({name})')
            self.cursor.execute(
                "INSERT INTO jobs VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (identifier, name, purpose, job_type, metadata, frame_range, Status.PENDING, environment, dependencies, parameters)
            )
        except Exception as e:
            self.logger.error(f'Failed to create job {job} for reason: {e}')
            return False

        data = []
        for i, frame in enumerate(frames):
            data.append(
                (identifier, int(str(identifier) + str(i)), purpose, job_type, frame, Status.PENDING, environment, dependencies, parameters, 'None'))

        self.cursor.executemany(
            """
            INSERT INTO tasks VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            data
        )

        self.connection.commit()
        return True

    def get_jobs_by_status(self, status: Status):
        self.logger.debug(f'DB: selecting jobs by status {status}')
        query = """
        SELECT *
        FROM jobs
        WHERE Status = ?
        """
        matching_jobs = self.cursor.execute(query, (status, )).fetchall()
        return matching_jobs


if __name__ == '__main__':
    import time
    new_db = DB()
    new_db.connect()
    test_id = 4050259621
    print(list(new_db.get_tasks_by_status(test_id, Status.PENDING, column='Task_Id')))
