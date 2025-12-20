import logging
from typing import Any

import websockets

from envy.lib.core.message import Message, FunctionMessage, MessageTarget, MessageType, build_from_message_dict
from envy.lib.core.message_handler import MessageHandler
from envy.lib.utils.utils import get_applicable_clients

logger = logging.getLogger(__name__)


class ServerMessageHandler(MessageHandler):

    def __init__(self, host: Any, module: str):
        super().__init__(host, module)
        self.server = host

    async def _handle_message(self, m: Message | FunctionMessage) -> None:
        if m.type == MessageType.PASS_ON:
            try:
                await self._pass_on(m)
            except RuntimeError:
                logger.debug(f'Failed to pass on message {m}')

        elif m.target == MessageTarget.SERVER:
            if m.type == MessageType.FUNCTION_MESSAGE:
                await self._execute_function_message(m)

        elif m.target == MessageTarget.CONSOLE:
            await self._send_to_consoles(m)

    async def _pass_on(self, m: Message):
        logger.debug(f'Passing on message: ({m})')
        function_message = build_from_message_dict(m.data)
        classifier = m.message
        send_targets = get_applicable_clients(classifier, list(self.server.clients))
        await self._send_to_clients(send_targets, function_message)

    async def _send_to_consoles(self, message: (Message, FunctionMessage)) -> None:
        """
        send a network.message object to a console
        """

        for console in self.host.consoles:
            ws = self.host.consoles[console].socket
            encoded_message = message.encode()
            await ws.send(encoded_message)
            logger.debug(f'Send: {message} -> {console}')

    async def _send_to_clients(self, clients: list, message: (Message, FunctionMessage)) -> None:
        """
        sends a message to every client connected to the server
        """
        for client in clients:
            await self._send_to_client(client, message)

    async def _send_to_client(self, client_name: str, message: (Message, FunctionMessage)) -> None:
        """
        Send a network.message object to a client
        :raises RuntimeError: If the message failed to send
        """

        logger.debug(f'sending {message} to {client_name}')
        if client := self.host.clients.get(client_name) is None:
            logger.warning(f'Targeted client does not exist: {client_name}')
            raise RuntimeError(f'targeted client does not exist.')

        ws = client.socket
        json_message = message.encode()

        try:
            await ws.send(json_message)
        except (websockets.exceptions.ConnectionClosedError, websockets.ConnectionClosed, websockets.ConnectionClosedOK) as e:
            logger.debug(f'Failed to send message: {e}')
            raise RuntimeError(f'failed to send message to {client_name}')
