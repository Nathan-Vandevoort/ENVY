import json
import logging
import os
import sys
from datetime import datetime

import envy
from envy.lib.jobs.enums import Purpose
from envy.lib.utils.utils import DummyLogger

logger = logging.getLogger(__name__)


class Job:
    def __init__(self, name: str):
        """
        Creates an empty job object (str) name must be provided
        Contains attributes:
        name: (str)
        purpose: (jobs.enums.Purpose)
        type: (str)
        environment: (dict)
        dependencies: (list of dict)
        parameters: (dict)
        :param name: (str) name of job
        """
        self.name = name
        self.purpose = None
        self.type = None
        self.id = hash(os.getlogin() + name + str(datetime.now())) % (10**10)

        self.range = ""

        self.environment = {}
        self.dependencies = []
        self.parameters = {}

        self.allocation = 1

        self.metadata = {'Creation_Time': datetime.now().strftime('%d-%m-%Y %H-%M-%S'), 'Contributors': []}

    def set_purpose(self, purpose: Purpose) -> None:
        self.purpose = purpose

    def get_purpose(self) -> Purpose:
        return self.purpose

    def set_type(self, type_value) -> None:
        self.type = type_value

    def get_type(self) -> str:
        return self.type

    def set_dependencies(self, dependencies: dict) -> None:
        self.dependencies = dependencies

    def get_dependencies(self) -> list:
        return self.dependencies

    def set_parameters(self, parameters: dict) -> None:
        self.parameters = parameters

    def get_parameters(self) -> dict:
        return self.parameters

    def add_dependency(self) -> None:
        raise NotImplemented()

    def remove_dependency(self, name: str) -> bool:
        for i, dependency in enumerate(self.dependencies):
            dependency_name = dependency['Name']
            if dependency_name == name:
                self.dependencies.pop(i)
                return True
        return False

    def set_environment(self, environment: dict) -> None:
        self.environment = environment

    def get_environment(self) -> dict:
        return self.environment

    def set_name(self, name: str) -> None:
        self.name = str(name)

    def set_allocation(self, number: int) -> None:
        self.allocation = int(number)

    def get_allocation(self) -> int:
        return self.allocation

    def encode(self) -> str:
        return json.dumps(self.as_dict())

    def as_dict(self) -> dict:
        return_dict = {
            'Name': self.name,
            'Purpose': self.purpose,
            'Type': self.type,
            'ID': self.id,
            'Range': self.range,
            'Environment': self.environment,
            'Dependencies': self.dependencies,
            'Parameters': self.parameters,
            'Metadata': self.metadata,
            'Allocation': self.allocation,
        }
        return return_dict

    def set_meta(self, metadata: dict = None) -> None:
        if not metadata:
            self.metadata = {'Creation_Time': datetime.today().strftime('%d-%m-%Y'), 'Contributors': [__name__]}
            return

        else:
            self.metadata = metadata
            self.meta_add_contributor()
            return

    def meta_add_contributor(self):
        contributors = self.metadata['Contributors']
        contributors.append(sys.modules['__main__'].__file__)

    def set_meta_value(self, key: str, value: any) -> bool:
        if key not in self.metadata:
            return False
        self.metadata[key] = value
        return True

    def get_meta(self) -> dict:
        return self.metadata

    def set_range(self, range_value: str) -> None:
        self.range = range_value

    def get_range(self) -> str:
        return self.range

    def add_range(self, start: int, end: int, increment: int) -> None:
        self.range += f' {start}-{end}:{increment}'

    def set_id(self, new_id: str) -> None:
        self.id = new_id

    def get_id(self) -> int:
        return int(self.id)

    def range_as_list(self) -> list:
        ranges = self.range.lstrip().split(' ')
        return_list = []
        for frame_range in ranges:
            range_split = frame_range.split('-')
            start = int(float(range_split[0]))
            range_split = range_split[1].split(':')
            end = int(float(range_split[0])) + 1
            increment = int(float(range_split[1]))
            return_list.extend(range(start, end, increment))
        return return_list

    def write(self) -> None:
        folder_path = os.path.join(envy.__file__, 'Jobs', 'Jobs')
        json_file_path = os.path.join(folder_path, f'{self.name}_{datetime.today().strftime("%d-%m-%Y_%H-%M-%S")}.json')

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        with open(json_file_path, 'w') as job_file:
            json.dump(self.as_dict(), job_file, indent=4)
            job_file.close()

    def as_sqlite_compliant(self):
        return_dict = self.as_dict()
        name = return_dict['Name']
        purpose = return_dict['Purpose']
        job_type = return_dict['Type']
        job_id = return_dict['ID']
        job_range = return_dict['Range']
        environment = json.dumps(return_dict['Environment'])
        parameters = json.dumps(return_dict['Parameters'])
        metadata = json.dumps(return_dict['Metadata'])
        dependencies = json.dumps(return_dict['Dependencies'])
        allocation = return_dict['Allocation']

        return_dict = {
            'Name': name,
            'Purpose': purpose,
            'Type': job_type,
            'ID': job_id,
            'Range': job_range,
            'Environment': environment,
            'Parameters': parameters,
            'Metadata': metadata,
            'Dependencies': dependencies,
            'Allocation': allocation,
        }

        return return_dict

    def __str__(self):
        return self.name

    def __format__(self, format_spec):
        return self.name


def job_from_dict(job_as_dict: dict, logger: logging.Logger = None) -> Job:

    logger.debug(f'Building job from {job_as_dict}')
    # validate there is a Name and a Purpose and a Type
    if 'Name' not in job_as_dict:
        logger.warning(f'Name key cannot be found in {job_as_dict}')
        raise IndexError(f'Name key cannot be found in {job_as_dict}')

    if 'Purpose' not in job_as_dict:
        logger.warning(f'Purpose key cannot be found in {job_as_dict}')
        raise IndexError(f'Purpose key cannot be found in {job_as_dict}')

    if 'Type' not in job_as_dict:
        logger.warning(f'Type key cannot be found in {job_as_dict}')
        raise IndexError(f'Type key cannot be found in {job_as_dict}')

    if 'Metadata' not in job_as_dict:
        logger.warning(f'Metadata cannot be found in {job_as_dict}')
        raise IndexError(f'Metadata cannot be found in {job_as_dict}')

    if 'Range' not in job_as_dict:
        logger.warning(f'Range cannot be found in {job_as_dict}')
        raise IndexError(f'Range cannot be found in {job_as_dict}')

    if 'ID' not in job_as_dict:
        logger.warning(f'ID cannot be found in {job_as_dict}')
        raise IndexError(f'ID cannot be found in {job_as_dict}')

    name = job_as_dict['Name']
    purpose = job_as_dict['Purpose']
    job_type = job_as_dict['Type']
    metadata = job_as_dict['Metadata']
    new_range = job_as_dict['Range']
    new_id = job_as_dict['ID']
    allocation = job_as_dict['Allocation']

    environment = None
    dependencies = None
    parameters = None

    if 'Environment' in job_as_dict:
        environment = job_as_dict['Environment']

    if 'Dependencies' in job_as_dict:
        dependencies = job_as_dict['Dependencies']

    if 'Parameters' in job_as_dict:
        parameters = job_as_dict['Parameters']

    new_job = Job(name)
    new_job.set_purpose(purpose)
    new_job.set_type(job_type)
    new_job.set_environment(environment)
    new_job.set_dependencies(dependencies)
    new_job.set_parameters(parameters)
    new_job.set_meta(metadata=metadata)
    new_job.set_range(new_range)
    new_job.set_id(new_id)
    new_job.set_allocation(allocation)

    return new_job


def job_from_sqlite(job_as_sql_tuple: tuple, logger: logging.Logger = None) -> Job:
    logger = logger or DummyLogger()

    logger.debug('Building Job from sql tuple')

    job_id, name, purpose, job_type, metadata, job_range, status, environment, dependencies, parameters = (
        job_as_sql_tuple
    )

    metadata = json.loads(metadata)
    environment = json.loads(environment)
    dependencies = json.loads(dependencies)
    parameters = json.loads(parameters)

    new_job = Job(name)
    new_job.set_purpose(purpose)
    new_job.set_type(job_type)
    new_job.set_environment(environment)
    new_job.set_dependencies(dependencies)
    new_job.set_parameters(parameters)
    new_job.set_meta(metadata=metadata)
    new_job.set_range(job_range)
    new_job.set_id(job_id)

    return new_job
