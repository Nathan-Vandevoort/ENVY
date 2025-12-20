import logging

logger = logging.getLogger(__name__)


def init_logging() -> None:
    """Initialize logging for the package."""

    fmt = '[{asctime}][{module}.{funcName}][{levelname: <8}]  {message}'
    logging.basicConfig(format=fmt, datefmt='%I:%M:%S%p', style='{', force=True)
