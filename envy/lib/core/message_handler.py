from __future__ import annotations

import logging
import asyncio
import queue
from ast import PyCF_ALLOW_TOP_LEVEL_AWAIT

from envy.lib.network import message
from envy.lib.utils.utils import get_applicable_clients

logger = logging.getLogger(__name__)


class MessageHandler:
    def __init__(self):
        self._process_queue: queue.Queue = queue.Queue()
        self.module = 'self'

    def set_process_queue(self, process_queue: queue.Queue) -> None:
        self._process_queue = process_queue

    async def start(self):
        """Starts the execution loop"""

        logger.debug(f'Starting...')
        while True:
            # Creates a copy of the queue to run over so there are no race conditions
            # where the queue grows mid-loop.
            if self._process_queue.not_empty:
                process_list = list(self._process_queue.queue)
                self._process_queue.empty()
                end = False
                for m in process_list:
                    if m is None:
                        end = True
                        break
                    await self._handle_message(m)
                if end:
                    logger.debug('Breaking execution loop')
                    break
            await asyncio.sleep(.5)

    def stop(self):
        """
        Adds a stop value to the execution queue.
        This will not stop the Executor right away but rather when the executor gets to the stop value.
        """

        logger.debug(f'Stopping...')
        self._process_queue.put(None)

    async def _handle_message(self, m: message.Message | message.FunctionMessage) -> None:
        if m.get_type() == message.MessageType.FUNCTION_MESSAGE:
            await self._execute_function_message(m)

    async def _execute_function_message(self, m: message.FunctionMessage):
        function = m.as_function()
        try:
            async_function = f'await {self.module}.{function}'
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
            logger.error(f'{function}: {e}')
