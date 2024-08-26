from enum import Enum


class Message_Purpose(str, Enum):
    CLIENT = 'client'
    CONSOLE = 'console'
    PASS_ON = 'pass_on'
    HEALTH_CHECK = 'health_check'
    SERVER = 'server'
    SMALL_SERVER_ERROR = 'small_server_error'
    MEDIUM_SERVER_ERROR = 'medium_server_error'
    LARGE_SERVER_ERROR = 'large_server_error'
    FUNCTION_MESSAGE = 'function_message'

    def __str__(self):
        return self.value

    def __format__(self, format_spec):
        return self.value
