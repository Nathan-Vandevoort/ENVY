from typing import Any, Optional, Literal, Union
from envy.schema import Message


class RPCRequest(Message):
    kind: Literal["rpcrequest"] = "rpcrequest"
    func_name: str
    args: tuple[Any]
    kwargs: dict[Any, Any]


class RPCResponse(Message):
    kind: Literal["rpcresponse"] = "rpcresponse"
    func_name: str
    result: Optional[Any]
    error: Optional[str]
