from pydantic import BaseModel


class Message(BaseModel):
    """
    Base class of all messages.
    A message is something which can be serialized to json and sent over a websocket.
    """

    id: int
