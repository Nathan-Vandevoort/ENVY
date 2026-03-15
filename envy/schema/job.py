from contextlib import suppress
import re
import enum

from .base import Message
from .plugin import Plugin, PluginData


class FrameRange(Message):
    """
    A wrapper for a deadline frame range string.

    This class provides methods to more easily work with deadline frame range strings.
    """

    range: str

    def to_frame_list(self) -> tuple[float, ...]:

        frames = []
        frame_ranges = self.range.split(",")
        for frame_range in frame_ranges:
            with suppress(ValueError):
                frames.append(int(frame_range))
                continue

            if match := re.search(r"(\d+) *- *(\d+)(?: *: *(\d+))?", frame_range):
                start_frame = int(match.group(1))
                end_frame = int(match.group(2))
                step = int(match.group(3)) or 1
                frames.extend(range(start_frame, end_frame, step))

        return tuple(frames)


class Status(enum.Enum):
    RUNNING = enum.auto()  # Is actively running.
    PENDING = enum.auto()  # Is assignable.
    QUEUED = enum.auto()  # Will be assigned to the next available worker.
    FAILED = enum.auto()  # Has errored out.
    FINISHED = enum.auto()  # Finished successfully.


class Task(Message):
    """
    A Task is the smallest unit of work which can be assigned to a worker.
    """

    id: int
    frame_range: FrameRange
    progress: float = 0.0
    status: Status = Status.PENDING
    priority: int = 50
    message: str = ""


class Job(Message):
    """
    A Job which corresponds to a job entry in the database.

    A Job can have any number of Rasks.
    """

    id: int
    name: str
    status: Status = Status.PENDING
    progress: float = 0.0

    priority: int = 50
    batch_size: int = 1
    plugin: str
    plugin_data: PluginData

    tasks: tuple[Task, ...] = ()
    version: int
    message: str = ""
