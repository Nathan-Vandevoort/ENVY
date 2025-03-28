import logging

import websockets

from envy.lib.core.data import Client, ClientStatus
from envy.lib.network.message import Message, FunctionMessage
from envy.lib.network.message import MessageTarget

logger = logging.getLogger(__name__)


async def update_client_state(server, state: dict) -> None:
    status_string = state.get('status')
    if status_string:
        status = ClientStatus(status_string)
    else:
        status = None
    name = state.get('name')
    task_id = state.get('task_id')
    job_id = state.get('job_id')

    if None in (status, task_id, job_id, name):
        logger.debug(f'{status=}, {task_id=}, {job_id=}')
        raise ValueError(f'malformed state')

    client_state = server.clients[name]

    # Only update the attributes which will realistically update
    client_state.task_id = task_id
    client_state.job_id = job_id
    client_state.status = status


async def send_client_state(server, client: str) -> None:
    client_data = server.clients.get(client)
    if not client_data:
        raise ValueError(f'client does not exist')


async def send_to_console(server, console: str, message: (Message, FunctionMessage)) -> None:
    """
    send a network.message object to a console
    """
    server.logger.debug(f'sending message: {message} to console: {console}')
    ws = server.consoles[console]['Socket']
    encoded_message = message.encode()
    await ws.send(encoded_message)


async def send_to_client(server, client_name: str, message: (Message, FunctionMessage)) -> None:
    """
    Send a network.message object to a client
    :raises RuntimeError: If the message failed to send
    """

    server.logger.debug(f'sending {message} to {client_name}')
    if client := server.clients.get(client_name) is None:
        logger.warning(f'Targeted client does not exist: {client_name}')
        raise RuntimeError(f'targeted client does not exist.')

    ws = client.socket
    json_message = message.encode()

    try:
        await ws.send(json_message)
    except (websockets.exceptions.ConnectionClosedError, websockets.ConnectionClosed, websockets.ConnectionClosedOK) as e:
        logger.debug(f'Failed to send message: {e}')
        raise RuntimeError(f'failed to send message to {client_name}')


async def send_to_consoles(server, message: (Message, FunctionMessage)) -> None:
    """
    sends a message to every console connected to the server
    """
    for console in server.consoles:
        try:
            await send_to_console(server, console, message)
        except KeyError:
            continue


async def send_to_clients(server, clients: list, message: (Message, FunctionMessage)) -> None:
    """
    sends a message to every client connected to the server
    """
    for client in clients:
        await send_to_client(server, client, message)


async def mark_task_as_finished(server, task_id: int) -> None:
    """
    Marks a task as finished in the scheduler
    """
    new_message = FunctionMessage('mark_task_as_finished()')
    new_message.set_target(MessageTarget.CONSOLE)
    new_message.set_function('mark_task_as_finished')
    new_message.format_arguments(task_id)
    await send_to_consoles(server, new_message)
    await server.job_scheduler.finish_task(task_id)


async def mark_job_as_finished(server, job_id: int, from_console: bool = False) -> None:
    new_message = FunctionMessage('mark_job_as_finished()')
    new_message.set_target(MessageTarget.CONSOLE)
    new_message.set_function('mark_job_as_finished')
    new_message.format_arguments(job_id)
    await send_to_consoles(server, new_message)
    await server.job_scheduler.finish_job(job_id, stop_workers=from_console)


async def mark_allocation_as_finished(server, allocation_id: int, from_console: bool = False) -> None:
    """
    Marks an allocation of tasks as finished in the scheduler
    """
    new_message = FunctionMessage('mark_allocation_as_finished()')
    new_message.set_target(MessageTarget.CONSOLE)
    new_message.set_function('mark_allocation_as_finished')
    new_message.format_arguments(allocation_id)
    await send_to_consoles(server, new_message)
    await server.job_scheduler.finish_allocation(allocation_id, stop_workers=from_console)


async def mark_allocation_as_started(server, allocation_id: int, computer: str) -> None:
    new_message = FunctionMessage('mark_allocation_as_started()')
    new_message.set_target(MessageTarget.CONSOLE)
    new_message.set_function('mark_allocation_as_started')
    new_message.format_arguments(allocation_id, computer)
    await send_to_consoles(server, new_message)


async def mark_task_as_started(server, task_id: int, computer: str) -> None:
    """
    Marks a task as started in the scheduler
    """

    new_message = FunctionMessage('mark_task_as_started()')
    new_message.set_target(MessageTarget.CONSOLE)
    new_message.set_function('mark_task_as_started')
    new_message.format_arguments(task_id, computer)
    await send_to_consoles(server, new_message)
    await server.job_scheduler.start_task(task_id, computer)


async def console_sync_job(server, job_id: int) -> None:
    new_message = FunctionMessage('console_sync_job()')
    new_message.set_target(MessageTarget.CONSOLE)
    new_message.set_function('sync_job')
    new_message.format_arguments(job_id)
    await send_to_consoles(server, new_message)


async def console_register_client(server, client: str, client_data: dict) -> None:
    new_message = FunctionMessage(f'console_register_client() {client}')
    new_message.set_target(MessageTarget.CONSOLE)
    new_message.set_function('register_client')
    new_message.format_arguments(client, data=client_data)
    await send_to_consoles(server, new_message)


async def console_unregister_client(server, client: str) -> None:
    new_message = FunctionMessage(f'console_register_client() {client}')
    new_message.set_target(MessageTarget.CONSOLE)
    new_message.set_function('unregister_client')
    new_message.format_arguments(client)
    await send_to_consoles(server, new_message)


async def mark_task_as_failed(server, task_id: int, reason: str) -> None:
    new_message = FunctionMessage('mark_task_as_failed()')
    new_message.set_target(MessageTarget.CONSOLE)
    new_message.set_function('mark_task_as_failed')
    new_message.format_arguments(task_id, reason)
    await send_to_consoles(server, new_message)
    await server.job_scheduler.fail_task(task_id, reason)


async def mark_allocation_as_failed(server, allocation_id: int, reason: str) -> None:
    new_message = FunctionMessage('mark_allocation_as_failed()')
    new_message.set_target(MessageTarget.CONSOLE)
    new_message.set_function('mark_allocation_as_failed')
    new_message.format_arguments(allocation_id, reason)
    await send_to_consoles(server, new_message)
    await server.job_scheduler.fail_allocation(allocation_id, reason)


async def update_allocation_progress(server, allocation_id: int, progress: int) -> None:
    new_message = FunctionMessage('update_allocation_progress()')
    new_message.set_target(MessageTarget.CONSOLE)
    new_message.set_function('update_allocation_progress')
    new_message.format_arguments(allocation_id, progress)
    await send_to_consoles(server, new_message)
