import logging

from envy.lib.core.message import FunctionMessage, Message, MessageTarget, MessageType, build_from_message_dict

logger = logging.getLogger(__name__)

def test_build_message_from_dict():
    input_messages = (
        Message(
            name='test01',
            message_type=MessageType.PASS_ON,
            target=MessageTarget.CLIENT,
            message='This is the message',
            data=['some', 'data'],
        ),
        FunctionMessage(
            name='test02',
            target=MessageTarget.CLIENT,
            message='This is the message',
            data=['some', 'data'],
            function='execute',
            reason='Failed to format\tString\nWhichIsFormmated\tLikeThis',
        ),
        FunctionMessage(
            name='test03',
            target=MessageTarget.CLIENT,
            message='This is the message',
            data=['some', 'data'],
            function='execute2',
            reason='Failed to format',
        ),
    )

    attributes = ('name', 'message_type', 'target', 'message', 'data', 'function', 'args', 'kwargs')

    for message in input_messages:
        logger.info(f'Encoding: {message}')
        message_as_dict = message.as_dict()

        recreated_message = build_from_message_dict(message_as_dict)

        for attribute in attributes:
            original_attrib = getattr(message, attribute, None)
            recreated_attrib = getattr(recreated_message, attribute, None)

            logger.debug(f'Testing attribute: {attribute}')
            logger.debug(f'{original_attrib=}, {recreated_attrib=}')

            assert original_attrib == recreated_attrib


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_build_message_from_dict()
