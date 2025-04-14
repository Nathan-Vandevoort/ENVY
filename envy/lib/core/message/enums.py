import enum


class MessageType(str, enum.Enum):
    PASS_ON = enum.auto()
    ERROR = enum.auto()
    FUNCTION_MESSAGE = enum.auto()


class MessageTarget(str, enum.Enum):
    CLIENT = enum.auto()
    SERVER = enum.auto()
    CONSOLE = enum.auto()


class ClientMessageType(enum.Enum):
    START_PLUGIN = enum.auto()
    STOP_PLUGIN = enum.auto()
    GET_STATE = enum.auto()
    CANCEL_FRAME = enum.auto()
    CANCEL_TASK = enum.auto()


class ServerMessageType(enum.Enum):
    UPDATE_CLIENT_STATE = enum.auto()


class ConsoleMessageType(enum.Enum):
    UPDATE_CLIENT_STATE = enum.auto()
