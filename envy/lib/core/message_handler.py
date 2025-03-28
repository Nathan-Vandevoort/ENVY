from __future__ import annotations

import asyncio
import importlib
import json
import logging
import queue
from ast import PyCF_ALLOW_TOP_LEVEL_AWAIT
from typing import Any

from envy.lib.network import message
from envy.lib.network.message import FunctionMessage

logger = logging.getLogger(__name__)

MODULE = None


class MessageHandler:
    def __init__(self, host: Any, module: str) -> None:
        """
        Initialize the message handler.
        :param module: The module the handler will attempt to access functions from.
        """

        self._process_queue: queue.Queue = queue.Queue()
        self.flush_interval = 0.5
        self.host = host
        self.module = module

    def set_process_queue(self, process_queue: queue.Queue) -> None:
        self._process_queue = process_queue

    def import_module(self) -> None:
        global MODULE
        MODULE = importlib.import_module(self.module)

    async def start(self) -> None:
        """Starts the execution loop"""

        self.import_module()
        if not MODULE:
            logger.error(f'Failed to load module {self.module}')
            raise RuntimeError(f'failed to load message module')

        logger.debug(f'Starting...')
        while True:
            while not self._process_queue.empty():
                m = self._process_queue.get()
                if m is None:
                    logger.debug('Breaking execution loop')
                    break
                await self._handle_message(m)

            await asyncio.sleep(self.flush_interval)

    def stop(self) -> None:
        """
        Adds a stop value to the execution queue.
        This will not stop the Executor right away but rather when the executor gets to the stop value.
        """

        logger.debug(f'Stopping...')
        self._process_queue.put(None)

    async def _handle_message(self, m: message.Message | message.FunctionMessage) -> None:
        if isinstance(m, message.FunctionMessage):
            await self._execute_function_message(m)
        else:
            logger.debug(f'Ignoring non function message')

    async def _execute_function_message(self, m: message.FunctionMessage) -> None:  # noqa
        function = as_function(m)
        if not function:
            logger.debug(f'Could not create function from message.')
            return

        try:
            async_function = f'await MODULE.{function}'
            logger.debug(f'Executing: {async_function}')
            code = compile(
                async_function,
                '<string>',
                'exec',
                flags=PyCF_ALLOW_TOP_LEVEL_AWAIT,
            )
            if coroutine := eval(code):
                await coroutine
        except Exception as e:
            logger.error(f'{function}: ', exc_info=e)


# TODO: This feels bad maybe this should go in a messages package
def as_function(m: FunctionMessage, inject_self: bool = True) -> str | None:
    """
    returns the string representation of the function payload to be used in functions like exec() or eval()
    This function will inject self to be the first argument by default unless the inject_self flag is off
    :return: (str) formatted function
    """

    # error out if function was never set
    if not m._function:
        return None

    # ensure types of args
    formatted_args = []
    for arg in m._args:
        validated_arg = arg

        if isinstance(arg, str):  # if you are a string make sure you have quotes
            validated_arg = f"'{arg}'"

        if isinstance(arg, dict):
            validated_arg = f"'{json.dumps(arg)}'"

        formatted_args.append(str(validated_arg))

    # if inject_self is true
    if inject_self:
        formatted_args.insert(0, 'self.host')

    # ensure types of kwargs
    formatted_kwargs = []
    for key, value in m._kwargs.items():
        processed_value = value

        if isinstance(value, str):  # if the value is a string make sure there are quotes
            processed_value = f"'{value}'"

        formatted_kwargs.append(f"{key}={processed_value}")

    formatted_args_string = ', '.join(formatted_args)
    formatted_kwargs_string = ', '.join(formatted_kwargs)
    complete_argument_string = ', '.join([formatted_args_string, formatted_kwargs_string])
    formatted_string = f"{m._function}({complete_argument_string})"

    return formatted_string
