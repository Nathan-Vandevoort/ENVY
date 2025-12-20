from typing import Type, TypeVar
import logging
import json
import dataclasses
import enum

from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ClientStatus(enum.Enum):
    IDLE = enum.auto()
    WORKING = enum.auto()
    STOPPED = enum.auto()


@dataclasses.dataclass
class Client:
    name: str
    status: ClientStatus = dataclasses.field(metadata={'enum': ClientStatus})
    job_id: int | None = None
    task_id: int | None = None
    ip: str | None = None


@dataclasses.dataclass
class Console:
    ip: str
    socket: WebSocketServerProtocol = dataclasses.field(metadata={'ignore': True})


def to_json(dataclass) -> str:
    fields = dataclasses.fields(dataclass)
    as_dict = {}
    for field in fields:
        if field.metadata.get('ignore'):
            continue
        elif field.metadata.get('enum'):
            as_dict[field.name] = getattr(dataclass, field.name).value
        else:
            as_dict[field.name] = getattr(dataclass, field.name)
    return json.dumps(as_dict)


def from_json(class_type: Type[T], json_data: str) -> Type[T] | None:
    try:
        as_dict = json.loads(json_data)
    except json.JSONDecodeError as e:
        logger.error('Failed to decode json.')
        logger.debug(e)
        return None

    fields = dataclasses.fields(class_type)
    data = {}
    for field in fields:
        if field.metadata.get('ignore'):
            data[field.name] = None
        elif enum_type := field.metadata.get('enum'):
            data[field.name] = enum_type(as_dict.get(field.name))
        else:
            data[field.name] = as_dict.get(field.name)

    return class_type(**data)
