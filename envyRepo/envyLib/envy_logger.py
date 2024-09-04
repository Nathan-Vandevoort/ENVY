import os, logging

os.system('color')
class CustomFormatterANSI(logging.Formatter):
    # Define color codes
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    # Define format
    format = '%(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: yellow + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

class CustomFormatterHTML(logging.Formatter):
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
        logging.CRITICAL: bold_red + format
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def get_logger(stream=None, html=False, level=logging.DEBUG):
    handler = logging.StreamHandler(stream=stream)
    if html is True:
        handler.setFormatter(CustomFormatterHTML())
    else:
        handler.setFormatter(CustomFormatterANSI())
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger