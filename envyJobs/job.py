from enums import Purpose, Status, Condition
import json
from envyLib.envy_utils import DummyLogger
import logging


class Job:
    def __init__(self, name: str):
        """
        Creates an empty job object (str) name must be provided
        Contains attributes:
        name: (str)
        purpose: (envyJobs.enums.Purpose)
        type: (str)
        environment: (dict)
        dependencies: (list of dict)
        parameters: (dict)
        :param name: (str) name of job
        """
        self.name = name
        self.purpose = None
        self.type = None
        self.environment = {}
        self.dependencies = []
        self.parameters = {}

    def set_purpose(self, purpose: Purpose) -> None:
        self.purpose = purpose

    def get_purpose(self) -> Purpose:
        return self.purpose

    def set_type(self, type) -> None:
        self.type = type

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

    def add_dependency(self, name: str, target_job: str, condition: Condition, value = None) -> None:
        new_dependency = {
            'Name': name,
            'Target': target_job,
            'Condition': condition,
            'Value': value
        }
        self.dependencies.append(new_dependency)

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
        self.name = name

    def encode(self) -> str:
        return json.dumps(self.as_dict())

    def as_dict(self) -> dict:
        return_dict = {
            'Name': self.name,
            'Purpose': self.purpose,
            'Type': self.type,
            'Environment': self.environment,
            'Dependencies': self.dependencies,
            'Parameters': self.parameters
        }

    def __str__(self):
        return self.name

    def __format__(self, format_spec):
        return self.name


def job_from_dict(job_as_dict: dict, logger: logging.Logger = None) -> Job:
    logger = logger or DummyLogger()

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

    name = job_as_dict['Name']
    purpose = job_as_dict['Purpose']
    job_type = job_as_dict['Type']

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

    return new_job
