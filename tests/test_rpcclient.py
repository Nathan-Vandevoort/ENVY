import asyncio
import logging

from envy.api.server.api import RPCRequest, parse_request
from envy.schema import Task
from envy.schema.job import FrameRange

logger = logging.getLogger(__name__)


async def test_rpc_request() -> None:
    task = Task(
        id=123456,
        frame_range=FrameRange(range="1-100"),
        message="testing",
    )

    message = RPCRequest(func_name="echo_task", args=(task,), kwargs={"message": "test_message"})
    data = message.model_dump()

    request = parse_request(data)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(test_rpc_request())
