import logging

from envy.lib.core.console.core import Console
from envy.lib.core.data import ClientStatus, Client
from envy.lib.core.message import Message, MessageTarget, MessageType

logger = logging.getLogger(__name__)


async def clients(console: Console) -> None:
    logger.info(f'Clients:')
    for client in console.clients:
        logger.info(console.clients[client])


async def register_clients(console: Console, clients: tuple[dict]) -> None:
    for client in clients:
        status_string = client.get('status')
        if status_string:
            status = ClientStatus(status_string)
        else:
            status = None
        name = client.get('name')
        task_id = client.get('task_id')
        job_id = client.get('job_id')

        if None in (status, task_id, job_id, name):
            logger.debug(f'{status=}, {task_id=}, {job_id=}, {name=}')
            raise ValueError(f'malformed state')

        logger.debug(f'Registering client: {name}')
        new_client = Client(
            name=name,
            status=status,
            job_id=job_id,
            task_id=task_id,
        )
        console.clients[name] = new_client


async def unregister_clients(console: Console, clients: tuple[str]) -> None:
    for client in clients:
        logger.debug(f'Unregistering client: {client}')
        if client in console.clients:
            del console.clients[client]


async def update_client(console: Console, states: tuple[dict]) -> None:
    for state in states:
        status_string = state.get('status')
        if status_string:
            status = ClientStatus(status_string)
        else:
            status = None
        name = state.get('name')
        task_id = state.get('task_id')
        job_id = state.get('job_id')

        if None in (status, task_id, job_id, name):
            logger.debug(f'{status=}, {task_id=}, {job_id=}, {name=}')
            raise ValueError(f'malformed state')

        client_state = console.clients[name]

        # Only update the attributes which will realistically update
        client_state.task_id = task_id
        client_state.job_id = job_id
        client_state.status = status


async def get_state(console: Console, client: str = None) -> None:
    if not client:
        client = await console.input('Which client:')

    new_message = FunctionMessage(
        f'Get state: {client}',
        target=MessageTarget.SERVER,
        function='send_client_state',
        client=client,
        console=console.name,
    )
    console.send(new_message)


async def send_to_clients(console: Console, classifier: str, function_message: FunctionMessage) -> None:
    """
    Sends a single message to the server with a message.FunctionMessage within.
    the server will then send copies of the function message to any clients which meet the classifier
    """

    message = Message(
        f'Pass on: {function_message}',
        message_type=MessageType.PASS_ON,
        data=function_message.as_dict(),
        message=classifier,
        target=MessageTarget.SERVER,
    )
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
