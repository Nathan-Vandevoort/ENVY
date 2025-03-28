import logging
from typing import Any

from envy.Plugins import Server_Functions
from envy.lib.core.message_handler import MessageHandler
from envy.lib.network import message
from envy.lib.utils.utils import get_applicable_clients

logger = logging.getLogger(__name__)


class ServerMessageHandler(MessageHandler):

    def __init__(self, host: Any, module: str):
        super().__init__(host, module)
        self.server = host

    async def _handle_message(self, m: message.Message | message.FunctionMessage) -> None:
        if m.get_type() == message.MessageType.FUNCTION_MESSAGE:
            await self._execute_function_message(m)

        elif m.get_type() == message.MessageType.PASS_ON:
            try:
                await self._pass_on(m)
            except RuntimeError:
                logger.debug(f'Failed to pass on message {m}')

    async def _pass_on(self, m: message.Message):
        logger.debug(f'Passing on message: ({m})')
        function_message = message.build_from_message_dict(m.get_data())
        classifier = m.get_message()
        send_targets = get_applicable_clients(classifier, list(self.server.clients))
        await Server_Functions.send_to_clients(self, send_targets, function_message)
