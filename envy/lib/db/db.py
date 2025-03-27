import json
import logging
import os
import sqlite3

import envy
from envy.lib.jobs import job as j
from envy.lib.jobs.enums import Status
from envy.lib.utils import utils as eutils

logger = logging.getLogger(__name__)


class DB:
    def __init__(self, path: str):
        self.connection = None
        self.cursor = None
        self.db_path = path

    def connect(self) -> None:
        logger.debug(f'connecting...')
        self.connection = sqlite3.connect(self.db_path, timeout=10)
        self.connection.execute("PRAGMA foreign_keys = 1")
        self.cursor = self.connection.cursor()
        logger.debug('connected to database')

    def disconnect(self) -> None:
        self.connection.close()

    def configure_db(self):
        logger.info('configuring database')

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS server(
            Id INTEGER PRIMARY KEY CHECK (Id = 1),
            server TEXT UNIQUE,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs
            (Id INTEGER PRIMARY KEY,
            Name TEXT NOT NULL,
            Allocation_Ids TEXT,
            Purpose TEXT,
            Metadata TEXT, 
            Type TEXT, 
            Environment TEXT,
            Parameters TEXT,
            Range TEXT, 
            Status TEXT, 
            Dependencies TEXT,
            Allocation INTEGER,
            Info Text)
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS allocations
            (Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Job_Id INTEGER,
            Task_Ids TEXT,
            Computer TEXT,
            Status TEXT,
            Info TEXT,
            FOREIGN KEY(Job_Id) REFERENCES jobs(Id))
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks
            (Id INTEGER PRIMARY KEY AUTOINCREMENT, 
            Job_Id INTEGER,
            Allocation_Id INTEGER,
            Frame INTEGER, 
            Status TEXT, 
            Computer TEXT,
            FOREIGN KEY(Allocation_Id) REFERENCES allocations(Id))
            """
        )

    def start(self):
        self.connect()
        self.configure_db()

    def acquire_lock(self, ip):
        """
        Acquires the database lock.
        :raises IOError: If the lock could not be acquired.
        """
        try:
            self.cursor.execute('INSERT INTO server (Id, server) VALUES (1, ?) ON CONFLICT(Id) DO UPDATE SET server=?, timestamp=CURRENT_TIMESTAMP', (ip, ip))
        except sqlite3.Error as e:
            raise IOError(f'Failed to acquire database lock: {e}')

    def maintain_lock(self, ip) -> None:
        self.cursor.execute('UPDATE server SET timestamp=CURRENT_TIMESTAMP WHERE server=?', (ip,))
        self.connection.commit()

    def add_job(self, job: j.Job) -> int | None:
        """
        Adds a job to the database including creating allocation and task entries.
        :param job: The Job object to add
        :return: (int) The new jobs ID or None if adding the job failed
        """
        logger.debug(f'DB: Adding Job {job}')
        job_id = self.create_job_entry(job)

        if job_id < 0:
            return None

        frame_list = job.range_as_list()
        allocation = job.get_allocation()
        allocations = eutils.split_list(frame_list, allocation)
        allocation_ids = []
        for alloc in allocations:
            allocation_id = self.create_allocation_entry(job, job_id)
            if allocation_id < 0:
                return None

            allocation_ids.append(allocation_id)

            task_ids = []
            for frame in alloc:
                task_id = self.create_task_entry(job, job_id, allocation_id, frame)

                if task_id < 0:
                    return None

                task_ids.append(task_id)

            task_ids = json.dumps(task_ids)
            self.set_allocation_value(allocation_id, 'Task_Ids', task_ids)

        allocation_ids = json.dumps(allocation_ids)
        self.set_job_value(job_id, 'Allocation_Ids', allocation_ids)
        return job_id

    def create_job_entry(self, job: j.Job) -> int:
        sqlite_job = job.as_sqlite_compliant()
        name = sqlite_job['Name']
        job_id = job.get_id()
        purpose = sqlite_job['Purpose']
        metadata = sqlite_job['Metadata']
        job_type = sqlite_job['Type']
        environment = sqlite_job['Environment']
        parameters = sqlite_job['Parameters']
        frame_range = sqlite_job['Range']
        dependencies = sqlite_job['Dependencies']
        allocation = sqlite_job['Allocation']

        logger.debug(f'DB: sqlite_job -> {sqlite_job} - ID -> {job_id}')

        # create job
        try:
            logger.debug(f'DB: Creating Job Entry')
            self.cursor.execute(
                "INSERT INTO jobs VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    job_id,
                    name,
                    '',
                    purpose,
                    metadata,
                    job_type,
                    environment,
                    parameters,
                    frame_range,
                    Status.PENDING,
                    dependencies,
                    allocation,
                    '',
                ),
            )
            self.connection.commit()
            return job_id
        except Exception as e:
            logger.error(f'Failed to create job {job} for reason: {e}')
            return -1

    def create_allocation_entry(self, job: j.Job, job_id: int) -> int:
        try:
            self.cursor.execute("INSERT INTO allocations VALUES(?, ?, ?, ?, ?, ?)", (None, job_id, '', '', Status.PENDING, ''))
            self.connection.commit()
            return self.cursor.lastrowid
        except Exception as e:
            logger.error(f'Failed to create allocation {job} for reason: {e}')
            return -1

    def create_task_entry(self, job: j.Job, job_id: int, allocation_id: int, frame: int):
        sqlite_job = job.as_sqlite_compliant()
        purpose = sqlite_job['Purpose']
        job_type = sqlite_job['Type']
        environment = sqlite_job['Environment']
        parameters = sqlite_job['Parameters']
        try:
            self.cursor.execute("INSERT INTO tasks VALUES(?, ?, ?, ?, ?, ?)", (None, job_id, allocation_id, frame, Status.PENDING, None))
            self.connection.commit()
            return self.cursor.lastrowid
        except Exception as e:
            logger.error(f'Failed to create task {job} for reason: {e}')
            return -1

    def set_task_value(self, task_id: int, column: str, value: any) -> None:

        query = f"""
        UPDATE tasks
        SET {column} = ?
        WHERE Id = ?
        """
        self.cursor.execute(query, (value, task_id))
        self.connection.commit()

    def set_job_value(self, job_id: int, column: str, value: any) -> None:

        query = f"""
        UPDATE jobs
        SET {column} = ?
        WHERE Id = ?
        """
        self.cursor.execute(query, (value, job_id))
        self.connection.commit()

    def set_allocation_value(self, allocation_id: int, column: str, value: any) -> None:

        query = f"""
                UPDATE allocations
                SET {column} = ?
                WHERE Id = ?
                """
        self.cursor.execute(query, (value, allocation_id))
        self.connection.commit()

    def get_task_value(self, task_id: int, column: str) -> any:

        query = f"""
        SELECT {column}
        FROM tasks
        WHERE Id = ?
        """
        self.cursor.execute(query, (task_id,))
        result = self.cursor.fetchone()

        if result is not None:

            return result[0]

        else:

            raise IndexError('Column does not exist')

    def get_task_values(self, task_id: int) -> tuple:

        query = f"""
        SELECT *
        FROM tasks
        WHERE Id = ?
        """
        self.cursor.execute(query, (task_id,))
        result = self.cursor.fetchone()

        if result is not None:

            return result
        else:

            raise IndexError('Column does not exist')

    def get_allocation_value(self, allocation_id: int, column: str) -> any:

        query = f"""
        SELECT {column}
        FROM allocations
        WHERE Id = ?
        """
        self.cursor.execute(query, (allocation_id,))
        result = self.cursor.fetchone()
        if result is not None:
            return result[0]
        else:

            raise IndexError('Column does not exist')

    def get_allocation_values(self, allocation_id: int) -> tuple:

        query = f"""
        SELECT *
        FROM allocations
        WHERE Id = ?
        """
        self.cursor.execute(query, (allocation_id,))
        result = self.cursor.fetchone()

        if result is not None:
            return result
        else:

            raise IndexError('Column does not exist')

    def get_job_value(self, job_id: int, column: str) -> any:

        query = f"""
        SELECT {column}
        FROM jobs
        WHERE Id = ?
        """
        self.cursor.execute(query, (job_id,))
        result = self.cursor.fetchone()

        if result is not None:

            return result[0]
        else:

            raise IndexError('Column does not exist')

    def get_job_values(self, job_id: int) -> tuple:

        query = f"""
        SELECT *
        FROM jobs
        WHERE Id = ?
        """
        self.cursor.execute(query, (job_id,))
        result = self.cursor.fetchone()

        if result is not None:

            return result
        else:

            raise IndexError('Column does not exist')

    def get_ids_by_value(self, table: str, column: str, value: any) -> tuple:

        query = f"""
        SELECT Id
        FROM {table}
        WHERE {column} = ?
        """
        self.cursor.execute(query, (value,))
        result = self.cursor.fetchall()

        if result is not None:

            return result
        else:

            raise IndexError('Column does not exist')

    def get_allocation_ids(self, job_id: int) -> list:

        query = f"""
        SELECT Allocation_Ids
        FROM jobs
        WHERE Id = ?
        """
        self.cursor.execute(query, (job_id,))
        result = self.cursor.fetchone()
        if isinstance(result, tuple):
            result = result[0]
        return json.loads(result)

    def get_task_ids(self, allocation_id: int) -> list:

        query = f"""
                SELECT Task_Ids
                FROM allocations
                WHERE Id = ?
                """
        self.cursor.execute(query, (allocation_id,))
        result = self.cursor.fetchone()[0]

        return json.loads(result)
