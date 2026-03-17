import inspect
import logging
from pydantic import BaseModel, create_model
from typing import Any, Callable

from functools import partial

from envy.schema import Job, Task
from envy.server.network.base import Server

from ..data import RPCRequest

logger = logging.getLogger(__name__)


class RPCClient:

    server: Server | None = None
    _model_cache: dict[str, type[BaseModel]] = {}

    async def echo_job_properties(self, job: Job, message="something") -> None:
        message = self._format_message("echo_job_properties", job, message=message)
        return await self._send_message(message)

    async def echo_task(self, task: Task, message="something") -> None:
        message = self._format_message("echo_task", task, message=message)
        return await self._send_message(message)

    def _format_message(self, func_name: str, *args, **kwargs) -> RPCRequest:
        envelope = RPCRequest(func_name=func_name, args=args, kwargs=kwargs)
        return envelope

    async def _send_message(self, message: RPCRequest) -> Any:
        if not self.server:
            raise ValueError("a server must be registered before calling the API")

        return await self.server.send(message)

    def register_server(self, server: Server) -> None:
        self.server = server

    @classmethod
    def get_validation_model(cls, func_name: str) -> type[BaseModel]:
        if model := cls._model_cache.get(func_name):
            return model

        methods = [name for name in dir(cls) if not name.startswith("__")]
        if func_name not in methods:
            raise ValueError(f"{func_name!r} is not a method of {cls.__name__!r}")

        func = getattr(cls, func_name)
        sig = inspect.signature(func)

        fields = {}
        for name, param in sig.parameters.items():
            if param.annotation is inspect.Parameter.empty:
                annotation = Any
            else:
                annotation = param.annotation

            default = ... if param.default is inspect.Parameter.empty else param.default
            fields[name] = (annotation, default)

        model = create_model(f"{func_name}_args", **fields)
        cls._model_cache[func_name] = model

        return model


def parse_request(payload: dict) -> Callable:
    func_name = payload.get("func_name")
    if not func_name:
        raise ValueError(f'Message with id {payload.get("message_id", "")!r} does not have a function_name field.')

    func = getattr(RPCClient, func_name, None)
    if not func:
        raise ValueError(f"{RPCClient.__name__!r} has no method {func_name!r}")

    sig = inspect.signature(func)
    bound = sig.bind(*payload["args"], **payload["kwargs"])

    model = RPCClient.get_validation_model(func_name)
    args = model.model_validate(bound.arguments)
    validated_arguments = {field: getattr(args, field) for field in model.model_fields}

    return partial(func, **validated_arguments)
