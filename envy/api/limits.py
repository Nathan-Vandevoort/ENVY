from __future__ import annotations

from pydantic import BaseModel, Field


class Limits(BaseModel):
    machines: int = Field(default=0)  # 0 is infinite.
    time: float = Field(default=0)  # in minutes, 0 is infinite.
    concurrent_tasks: int = Field(default=0)  # 0 is as many as required.


class Range(BaseModel):
    start: float
    end: float
    step: float
