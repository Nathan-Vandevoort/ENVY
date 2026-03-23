from abc import ABC
import inspect
import logging
from pydantic import BaseModel, create_model, TypeAdapter, type_adapter
from typing import Any, Callable

from functools import partial

from envy.api.data import RPCRequest, RPCResponse

from ..exceptions import RPCError


logger = logging.getLogger(__name__)


class RPCBase(ABC):

    _model_cache: dict[str, type[BaseModel]] = {}

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

    @classmethod
    def parse_request(cls, payload: dict) -> Callable:
        func_name = payload.get("func_name")
        if not func_name:
            raise ValueError(f'Message with id {payload.get("message_id", "")!r} does not have a function_name field.')

        func = getattr(cls, func_name, None)
        if not func:
            raise ValueError(f"{cls.__name__!r} has no method {func_name!r}")

        sig = inspect.signature(func)
        bound = sig.bind(*payload["args"], **payload["kwargs"])

        model = cls.get_validation_model(func_name)
        args = model.model_validate(bound.arguments)
        validated_arguments = {field: getattr(args, field) for field in model.model_fields}

        return partial(func, **validated_arguments)

    @classmethod
    def parse_response(cls, payload: dict) -> Any | RPCError:
        func_name = payload.get("func_name")
        if not func_name:
            raise ValueError(f'Message with id {payload.get("message_id", "")!r} does not have a function_name field.')

        func = getattr(cls, func_name, None)
        if not func:
            raise ValueError(f"{cls.__name__!r} has no method {func_name!r}")

        if error := payload.get("error"):
            return RPCError(error)

        # If there is no exception there must be a result.
        result = payload["result"]

        sig = inspect.signature(func)
        return_type = sig.return_annotation

        if return_type is None or return_type is type(None):
            if result is not None:
                raise ValueError(f"method {func_name!r} returned {result!r} but is annotated to return None.")
            return None

        adapter = TypeAdapter(return_type)

        return adapter.validate_json(result)
