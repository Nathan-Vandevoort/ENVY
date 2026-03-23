import logging
from typing import Any

from envy.schema import Job, Task
from envy.server.network.base import Server as NetworkingServer

from ..data import RPCRequest
from ..base import RPCBase

logger = logging.getLogger(__name__)


class Server:

    async def echo_task(self, task: Task, message="something") -> Task:
        return task


class RPCServer(RPCBase):

    server: NetworkingServer | None = None

    async def echo_job_properties(self, job: Job, message="something") -> str:
        message = self._format_message("echo_job_properties", job, message=message)

        return await self._send_message(message)

    async def echo_task(self, task: Task, message="something") -> None:
        message = self._format_message("echo_task", task, message=message)

        return await self._send_message(message)

    async def _send_message(self, message: RPCRequest) -> Any:
        if not self.server:
            raise ValueError("a server must be registered before calling the API")

        return await self.server.send(message)

    def _format_message(self, func_name: str, *args, **kwargs) -> RPCRequest:
        envelope = RPCRequest(func_name=func_name, args=args, kwargs=kwargs)
        return envelope
