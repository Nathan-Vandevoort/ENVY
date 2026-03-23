import logging
from typing import Any

from envy.schema import Task
from envy.server.network.base import Server

from ..data import RPCRequest
from ..base import RPCBase

logger = logging.getLogger(__name__)


class Console: ...


class RPCConsole(RPCBase):

    def __init__(self, server: Server, name: str, ip: str) -> None:
        self.server = server
        self.name = name
        self.ip = ip

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
