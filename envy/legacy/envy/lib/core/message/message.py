from __future__ import annotations

import dataclasses
import logging
import json

from .enums import MessageTarget, MessageType

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Message:
    message_type: MessageType
    message_target: MessageTarget
    function: str
    data: dict = {}
    args: list = []
    kwargs: dict = {}

    def encode(self) -> str:
        message_data = {
            "Message_Type": self.message_type.value,
            "Target": self.message_target.value,
            "Data": self.data,
            "function": self.function,
            "args": self.args,
            "kwargs": self.kwargs,
        }

        try:
            encoded_message_data = json.dumps(message_data, indent=4)
        except TypeError as e:
            logger.error("Failed to serialize message")
            raise TypeError from e

        return encoded_message_data

    def as_function(self, inject_self: bool = True) -> str:
        """
        returns the string representation of the function payload to be used in functions like exec() or eval()
        This function will inject self to be the first argument by default unless the inject_self flag is off
        :return: (str) formatted function
        """

        formatted_args = []
        if inject_self:
            formatted_args.insert(0, 'self')

        # ensure types of args
        for arg in self.args:
            validated_arg = arg
            if isinstance(arg, str):  # if you are a string make sure you have quotes
                validated_arg = f"'{arg}'"
            if isinstance(arg, dict):
                validated_arg = f"'{json.dumps(arg)}'"
            formatted_args.append(str(validated_arg))

        # ensure types of kwargs
        formatted_kwargs = []
        for key, value in self.kwargs.items():
            processed_value = value
            if isinstance(value, str):  # if the value is a string make sure there are quotes
                processed_value = f"'{value}'"
            formatted_kwargs.append(f"{key}={processed_value}")

        formatted_args_string = ', '.join(formatted_args)
        formatted_kwargs_string = ', '.join(formatted_kwargs)
        complete_argument_string = ', '.join([formatted_args_string, formatted_kwargs_string])
        function_string = f"{self.function}({complete_argument_string})"

        return function_string

    @staticmethod
    def decode(encoded_message_data: str) -> Message | None:

        try:
            message_data = json.loads(encoded_message_data)
        except json.JSONDecodeError:
            logger.error("Failed to decode message.")
            logger.debug(f"{encoded_message_data}")
            return None

        message_type = message_data.get("Message_Type")
        message_target = message_data.get("Message_Target")
        function = message_data.get("Message_Function")
        data = message_data.get("Message_Data")
        args = message_data.get("args")
        kwargs = message_data.get("kwargs")

        # Exclude args and kwargs from the check because they aren't necessary.
        datas = (message_type, message_target, function, data)
        idx = datas.index(None) if None in datas else None
        if idx:
            logger.error("None value in message data.")
            logger.debug(f"{datas=}")
            return None

        # Rebuild enums.
        try:
            message_type = MessageType(message_type)
            message_target = MessageTarget(message_target)
        except ValueError:
            logger.error("Failed to rebuild enums.")
            logger.debug(f"{message_type=}, {message_target=}")
            return None

        new_message = Message(
            message_type=message_type,
            message_target=message_target,
            function=function,
            data=data,
            args=args,
            kwargs=kwargs,
        )

        return new_message
