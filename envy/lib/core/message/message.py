from __future__ import annotations

from typing import Any

from .enums import MessageType, MessageTarget

import json
import logging

logger = logging.getLogger(__name__)


class Message:

    def __init__(
        self,
        name: str,
        message_type: MessageType,
        target: MessageTarget,
        message: Any,
        data: Any = None,
    ):
        self.name = name
        self.type: MessageType = message_type
        self.target = target
        self.message = message
        self.data = data

    def encode(self) -> str:
        """
        encodes the current message object into a json string
        """
        message_dict = self.as_dict()
        json_string = json.dumps(message_dict)
        return json_string

    def as_dict(self) -> dict:
        """
        returns the current state of the Message object as a dictionary
        :return: dict version of message
        """
        result = {
            'Message_Purpose': self.type,
            'Message': self.message,
            'Name': self.name,
            'Data': self.data,
            'Target': self.target,
        }
        return result

    def __format__(self, format_spec):
        return self.name


class FunctionMessage(Message):
    def __init__(
        self,
        name: str,
        target: MessageTarget,
        function: str,
        message: Any = None,
        data: Any = None,
        *args,
        **kwargs,
    ):
        super().__init__(name, message_type=MessageType.FUNCTION_MESSAGE, target=target, message=message, data=data)
        self.function: str = function
        self.args = args
        self.kwargs = kwargs

    def as_dict(self) -> dict:
        """
        returns the current state of the message object as a dictionary
        :return: (dict) representation of FunctionMessage object
        """
        return_dict = {
            'Message_Purpose': self.type,
            'Message': self.message,
            'Name': self.name,
            'Target': self.target,
            'Function': self.function,
            'Args': self.args,
            'Kwargs': self.kwargs,
            'Data': self.data,
        }
        return return_dict

    def as_function(self, inject_self: bool = True) -> str:
        """
        returns the string representation of the function payload to be used in functions like exec() or eval()
        This function will inject self to be the first argument by default unless the inject_self flag is off
        :return: (str) formatted function
        """

        # error out if function was never set
        if not self.function:
            raise ValueError('Function was never set')

        # ensure types of args
        formatted_args = []
        for arg in self.args:
            validated_arg = arg

            if isinstance(arg, str):  # if you are a string make sure you have quotes
                validated_arg = f"'{arg}'"

            if isinstance(arg, dict):
                validated_arg = f"'{json.dumps(arg)}'"

            formatted_args.append(str(validated_arg))

        # if inject_self is true
        if inject_self:
            formatted_args.insert(0, 'self')

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
        formatted_string = f"{self.function}({complete_argument_string})"

        return formatted_string


def build_from_message_dict(input_dict: dict) -> Message | FunctionMessage:
    """
    Given a dictionary which was created from a message object, build a new message object with payload set to message from the dict
    :param input_dict: (dict) a dictionary which represents a message object
    :return: Message or FunctionMessage

    :raises ValueError: If the input is invalid dict cannot be turned into a message object
    """

    logger.debug(f'input_dict: {input_dict}')
    if 'Message_Purpose' not in input_dict:
        raise ValueError(f'Message_Purpose Key cannot be found in {input_dict}, are you sure this is a message dictionary?')

    if 'Message' not in input_dict:
        raise ValueError(f'Message Key cannot be found in {input_dict}, are you sure this is a message dictionary?')

    purpose = input_dict['Message_Purpose']
    message = input_dict['Message']
    name = input_dict['Name']
    data = input_dict['Data']
    target = input_dict['Target']

    # If purpose is Message_Purpose.Function_Message then return a FunctionMessage
    if purpose == MessageType.FUNCTION_MESSAGE:
        function = input_dict['Function']
        args = input_dict['Args']
        kwargs = input_dict['Kwargs']

        new_func_message = FunctionMessage(
            name,
            target=target,
            function=function,
            message=message,
            data=data,
        )

        # Set args and kwargs manually so unpacking doesn't try to read args as a keyword argument.
        new_func_message.args = args
        new_func_message.kwargs = kwargs

        return new_func_message

    else:
        new_message = Message(
            name,
            message_type=purpose,
            message=message,
            data=data,
            target=target,
        )
        return new_message
