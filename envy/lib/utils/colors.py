from enum import Enum
import os


class Colors(str, Enum):
    WHITE = '\033[0;37;40m'
    RED = '\033[0;31;40m'
    CLEAR = '\033[0;0m'
    CYAN = '\033[0;36;40m'
    PURPLE = '\033[0;35;40m'
    BLACK = '\033[0;30;40m'
    GREEN = '\033[0;32;40m'
    YELLOW = '\033[0;33;40m'
    BLUE = '\033[0;34;40m'
    IMPORTANT = '\033[0;37;41m'
    CLEAR_TERMINAL = '\033[2J'

    def __str__(self):
        return self.value

    def __format__(self, format_spec):
        return self.value


os.system('color')
