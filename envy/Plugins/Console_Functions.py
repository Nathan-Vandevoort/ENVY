import logging

from envy.lib.core.console.core import Console
from envy.lib.network import message as m
from envy.lib.network.message import MessageTarget, MessageType, FunctionMessage

logger = logging.getLogger(__name__)


async def debug(console: Console) -> None:
    logger.info('WAHOOOOOOOOOO')


async def get_state(console: Console, client: str = None) -> None:
    if not client:
        client = await console.input('Which client:')

    new_message = FunctionMessage(f'Get state: {client}')
    new_message.set_target(MessageTarget.CLIENT)
    new_message.set_function(f'send_client_state')
    new_message.format_arguments(target=console.name)

    console.send(new_message)


async def send_to_clients(console: Console, classifier: str, function_message: m.FunctionMessage) -> None:
    """
    Sends a single message to the server with a message.FunctionMessage within.
    the server will then send copies of the function message to any clients which meet the classifier
    """
    message = m.Message(f'Pass on: {function_message}')
    message.set_type(MessageType.PASS_ON)
    message.set_data(function_message.as_dict())
    message.set_message(classifier)
    console.send(message)


# async def install_maya_plugin(console) -> None:
#     """
#     installs the Maya plugin
#     :param console: reference to the console calling the function
#     """
#     maya_user_folder = 'Z:/maya'
#     envy_plugin_path = os.path.join(Config.ENVYPATH, 'Plugins', 'eMaya', 'envy.py')
#     console.logger.info(envy_plugin_path)
#     if not os.path.exists(maya_user_folder):
#         console.display_error('Maya plugin installation failed: Maya user folder not found.')
#         return
#     elif not os.path.exists(envy_plugin_path):
#         console.display_error('Maya plugin installation failed: Envy plugin not found.')
#         return
#
#     for folder in os.listdir(maya_user_folder):
#         if folder.isdigit():
#             maya_plugins_folder = os.path.join(maya_user_folder, folder, 'plug-ins')
#
#             if not os.path.exists(maya_plugins_folder):
#                 os.mkdir(maya_plugins_folder)
#
#             shutil.copy(envy_plugin_path, maya_plugins_folder)
#
#     console.display_info('Maya plugin installed successfully.')
#
