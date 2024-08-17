from enum import Enum


class Purpose(str, Enum):
    RENDER = 'render'
    CACHE = 'cache'
    SIMULATION = 'simulation'

    def __str__(self):
        return self.value

    def __format__(self, format_spec):
        return self.value


class Status(str, Enum):
    PENDING = 'pending'
    INPROGRESS = 'inprogress'
    DONE = 'done'
    IDLE = 'idle'
    WORKING = 'working'

    def __str__(self):
        return self.value

    def __format__(self, format_spec):
        return self.value


class Condition(str, Enum):
    ON_PENDING = 'on_pending'
    ON_INPROGRESS = 'on_inprogress'
    ON_DONE = 'on_done'
    ON_TIME = 'on_time'

    def __str__(self):
        return self.value

    def __format__(self, format_spec):
        return self.value
