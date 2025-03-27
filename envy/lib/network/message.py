from __future__ import annotations

import json
import logging
import enum

logger = logging.getLogger(__name__)


class MessageType(str, enum.Enum):
    PASS_ON = enum.auto()
    HEALTH_CHECK = enum.auto()
    ERROR = enum.auto()
    FUNCTION_MESSAGE = enum.auto()

    def __str__(self):
        return self.value

    def __format__(self, format_spec):
        return self.value


class MessageTarget(str, enum.Enum):
    CLIENT = enum.auto()
    SERVER = enum.auto()
    CONSOLE = enum.auto()

    def __str__(self):
        return self.value

    def __format__(self, format_spec):
        return self.value


class Message:

    def __init__(self, name: str):
        self._type: MessageType | None = None
        self._message = None
        self._data = None
        self._target = MessageTarget.CLIENT
        self.name = name

    def set_type(self, purpose: MessageType) -> None:
        """
        Sets the purpose of the message
        :param purpose: a selection from the network.purpose.Message_Purpose enum
        :return: Void
        """
        self._type = purpose

    def set_name(self, name: str) -> None:
        """
        sets the name attribute of message object
        :param name: (str) name to set to
        :return: Void
        """
        self.name = name

    def set_data(self, data: any) -> None:
        """
        sets the data field to any arbitrary data
        :param data: any
        :return: Void
        """
        self._data = data

    def get_data(self) -> any:
        """
        returns whatever is in the data field
        :return: (any) data
        """
        return self._data

    def get_type(self) -> MessageType:
        """
        Retrieves the current purpose and returns it
        :param self: reference to message object
        :return: Message Message_Purpose
        """
        return self._type

    def set_message(self, message: any) -> None:
        """
        Sets the message of the message object
        :param message: Data to set the message of the Message object to. This must be json serializable
        :return: Void
        """
        self._message = message

    def get_message(self) -> any:
        """
        Retrieves the current message and returns it
        :return: message
        """
        return self._message

    def encode(self) -> str:
        """
        encodes the current message object into a json string
        """
        message_dict = self.as_dict()
        json_string = json.dumps(message_dict)
        return json_string

    def get_target(self) -> MessageTarget:
        """
        returns the Target the function is intended to execute on
        :return: (network.Message_Purpose) Either Message_Purpose.CLIENT, Message_Purpose.CONSOLE, or Message_Purpose.SERVER
        """
        return self._target

    def set_target(self, target: MessageTarget) -> None:
        """
        Sets the target of the current function message
        The target is the desired end point for the payload of the function method to execute on
        eg: set_target(Message_Purpose.CLIENT) the function payload will only run on clients
        :param target: Either Message_Purpose.CLIENT, Message_Purpose.CONSOLE, or Message_Purpose.SERVER
        :return: Void
        """
        self._target = target

    def as_dict(self) -> dict:
        """
        returns the current state of the Message object as a dictionary
        :return: dict version of message
        """
        result = {
            'Message_Purpose': self._type,
            'Message': self._message,
            'Name': self.name,
            'Data': self._data,
            'Target': self._target,
        }
        return result

    def __str__(self):
        return self.name

    def __format__(self, format_spec):
        return self.name


class FunctionMessage(Message):
    def __init__(self, name):
        super().__init__(name)
        self._purpose = MessageType.FUNCTION_MESSAGE
        self._target = None
        self._function = None
        self._args = []
        self._kwargs = {}

    def set_function(self, function: str) -> None:
        """
        sets the function of the FunctionMessage object
        :param function: (str) function name
        :return:
        """
        self._function = function

    def set_args(self, args: list) -> None:
        """
        Sets the arguments list of the function payload it may be easier to use FunctionMessage.format_arguments()
        :param args: a list of arguments
        :return: Void
        """
        self._args = args

    def set_kwargs(self, kwargs: dict) -> None:
        """
        Sets the keyword arguments dictionary of the function payload it may be easier to use FunctionMessage.format_arguments()
        :param kwargs: a dictionary of keyword arguments and values
        :return: Void
        """
        self._kwargs = kwargs

    def get_function(self) -> str:
        """
        returns the name of the function stored within this object
        :return: (str) function name
        """
        return self._function

    def get_args(self) -> list:
        """
        returns the list of arguments inside the function payload
        :return: (list) of arguments
        """
        return self._args

    def get_kwargs(self) -> dict:
        """
        returns the dictionary of keyword arguments and values of the function payload
        :return: (dict) keyword arguments
        """
        return self._kwargs

    def as_dict(self) -> dict:
        """
        returns the current state of the message object as a dictionary
        :return: (dict) representation of FunctionMessage object
        """
        return_dict = {
            'Message_Purpose': self._purpose,
            'Message': self._message,
            'Name': self.name,
            'Target': self._target,
            'Function': self._function,
            'Args': self._args,
            'Kwargs': self._kwargs,
            'Data': self._data,
        }
        return return_dict

    def format_arguments(self, *args, **kwargs) -> None:
        """
        Provides an easier way to build the function payload simply input arguments and keyword arguments as you would into the end function
        :param args: any arbitrary arguments must be json serializable
        :param kwargs: any arbitrary keyword arguments must be json serializable
        :return: Void
        """
        self._args = args
        self._kwargs = kwargs

    def as_function(self, inject_self: bool = True) -> str:
        """
        returns the string representation of the function payload to be used in functions like exec() or eval()
        This function will inject self to be the first argument by default unless the inject_self flag is off
        :return: (str) formatted function
        """

        # error out if function was never set
        if not self._function:
            raise TypeError('Function was never set')

        # ensure types of args
        formatted_args = []
        for arg in self._args:
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
        for key, value in self._kwargs.items():
            processed_value = value

            if isinstance(value, str):  # if the value is a string make sure there are quotes
                processed_value = f"'{value}'"

            formatted_kwargs.append(f"{key}={processed_value}")

        formatted_args_string = ', '.join(formatted_args)
        formatted_kwargs_string = ', '.join(formatted_kwargs)
        complete_argument_string = ', '.join([formatted_args_string, formatted_kwargs_string])
        formatted_string = f"{self._function}({complete_argument_string})"

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

        new_func_message = FunctionMessage(name)
        new_func_message.set_target(target)
        new_func_message.set_message(message)
        new_func_message.set_args(args)
        new_func_message.set_kwargs(kwargs)
        new_func_message.set_function(function)
        new_func_message.set_data(data)

        return new_func_message

    else:
        new_message = Message(name)
        new_message.set_type(purpose)
        new_message.set_message(message)
        new_message.set_data(data)
        new_message.set_target(target)
        return new_message
