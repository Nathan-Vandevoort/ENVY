from __future__ import annotations

import enum
from typing import Any

from pydantic import Field

from .message import Message
from .limits import Limits, Range
from .plugin import Plugin


class Status(enum.Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'


class Task(Message):
    range: Range
    status: Status = Field(default=Status.PENDING)
    completed_frames: tuple[float, ...] = Field(default=())

    @property
    def order(self) -> float:
        return (self.range.start + self.range.end) * (1 / self.range.step)


class Job(Message):
    plugin: Plugin
    limits: Limits
    priority: int  # must be a range 0 - 100.
    status: Status = Field(default=Status.PENDING)
    dependencies: tuple[Job, ...] = Field(default=())
    tasks: tuple[Task, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default={})
