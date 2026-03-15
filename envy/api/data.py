from typing import Any, Optional
from envy.schema import Message


class RPCRequest(Message):
    func_name: str
    args: tuple[Any]
    kwargs: dict[Any, Any]


class RPCResponse(Message):
    result: Optional[Any]
    error: Optional[str]
