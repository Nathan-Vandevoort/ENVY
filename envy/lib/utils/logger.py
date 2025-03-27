import datetime
import logging


class ANSIFormatter(logging.Formatter):

    DEBUG = "\x1b[38;5;66m"
    INFO = "\x1b[38;5;255m"
    WARNING = "\x1b[38;5;220m"
    ERROR = "\x1b[38;5;196m"
    CRITICAL = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, prefix: str = None) -> None:
        super().__init__()

        if prefix:
            self.prefix = f'[{prefix}] '
        else:
            self.prefix = ''

    def format(self, record: logging.LogRecord):
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if record.levelno == logging.DEBUG:
            color = self.DEBUG
        elif record.levelno == logging.INFO:
            color = self.INFO
        elif record.levelno == logging.WARNING:
            color = self.WARNING
        elif record.levelno == logging.ERROR:
            color = self.ERROR
        elif record.levelno == logging.CRITICAL:
            color = self.CRITICAL
        else:
            color = self.INFO

        log = f'{color}{self.prefix}{time} - {record.name}.{record.funcName} - {record.levelname} - {record.getMessage()}{self.reset}'
        return log


class HTMLFormatter(logging.Formatter):
    # Define color codes
    purple = '<span style="color:#EE82EE">'
    black = '<span style="color:black">'
    yellow = '<span style="color:#FFD700">'
    red = '<span style="color:#CD5C5C">'
    bold_red = '<span style="color:#8B0000">'
    white = '<span style="color:white">'

    # Define format
    format = '%(levelname)s - [%(filename)s:%(lineno)d] - <span style="color:white">%(message)s'

    FORMATS = {
        logging.DEBUG: purple + format,
        logging.INFO: white + format,
        logging.WARNING: yellow + format,
        logging.ERROR: red + format,
        logging.CRITICAL: bold_red + format,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
