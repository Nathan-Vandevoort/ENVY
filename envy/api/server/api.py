from typing import Any

from envy.schema import Job
from envy.server.network.base import Server

from ..data import RPCRequest


class RPCClient:

    server: Server | None = None

    @classmethod
    async def echo_job_properties(cls, job: Job, message="something") -> None:
        message = cls._format_message("echo_job_properties", job, message=message)

    @classmethod
    def _format_message(cls, func_name: str, *args, **kwargs) -> RPCRequest:
        envelope = RPCRequest(func_name=func_name, args=args, kwargs=kwargs)
        return envelope

    @classmethod
    async def _send_message(cls, message: RPCRequest) -> Any:
        if not cls.server:
            raise ValueError("a server must be registered before calling the API")

        return await cls.server.send(message)

    @classmethod
    async def register_server(cls, server: Server) -> None:
        cls.server = server
