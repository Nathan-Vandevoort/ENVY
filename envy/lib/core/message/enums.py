import enum


class MessageType(str, enum.Enum):
    PASS_ON = enum.auto()
    HEALTH_CHECK = enum.auto()
    ERROR = enum.auto()
    FUNCTION_MESSAGE = enum.auto()

    def __str__(self):
        return self.value

    def __format__(self, format_spec):
        return self.value


class MessageTarget(str, enum.Enum):
    CLIENT = enum.auto()
    SERVER = enum.auto()
    CONSOLE = enum.auto()

    def __str__(self):
        return self.value

    def __format__(self, format_spec):
        return self.value
