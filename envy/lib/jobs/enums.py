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
    DIRTY = 'failed'
    IDLE = 'idle'
    WORKING = 'working'
    STOPPED = 'stopped'
    FAILED = 'failed'

    def __str__(self):
        return self.value

    def __format__(self, format_spec):
        return self.value

    def __json__(self):
        return self.value

