from enum import Enum
import json


class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return json.JSONEncoder.default(self, obj)


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
    DIRTY = 'dirty'
    IDLE = 'idle'
    WORKING = 'working'
    STOPPED = 'stopped'

    def __str__(self):
        return self.value

    def __format__(self, format_spec):
        return self.value

    def __json__(self):
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
