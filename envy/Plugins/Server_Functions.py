__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.4"

import sys, os
abs_file = os.path.abspath(__file__)
sys.path.append(os.path.join(os.path.dirname(abs_file), os.pardir, os.pardir))
from utils.config_bridge import Config
from envyRepo.networkUtils import message as m
from envyRepo.networkUtils.message_purpose import Message_Purpose
import json
__config__ = sys.modules.get('config_bridge')

async def send_to_console(server, console: str, message: (m.Message, m.FunctionMessage)) -> None:
    """
    send a networkUtils.message object to a console
    :param server: reference to server calling the function
    :param console: (str) name of console to send message to
    :param message: networkUtils.message object to send to client
    :return: Void
    """
    server.logger.debug(f'sending message: {message} to console: {console}')
    ws = server.consoles[console]['Socket']
    encoded_message = message.encode()
    await ws.send(encoded_message)


async def send_to_client(server, client: str, message: (m.Message, m.FunctionMessage)) -> None:
    """
    Send a networkUtils.message object to a client
    :param server: reference to server calling the function
    :param client: (str) name of client to send message to
    :param message: networkUtils.message object to send to client
    :return: Void
    """
    server.logger.debug(f'sending {message} to {client}')
    ws = server.clients[client]['Socket']
    json_message = message.encode()
    await ws.send(json_message)


async def send_attribute_to_client(server, client: str, attribute: str, buffer_name: str) -> None:
    """
    Sends the value of any attribute on the server object to any client
    :param server: reference to server calling the function
    :param client: (str) name of client to send message to
    :param attribute: (str) name of attribute to send
    :param buffer_name: (str) name of buffer on client you want to fill
    :return: Void
    """
    attribute = getattr(server, attribute)
    message = m.FunctionMessage(f'send_attribute_to_client(): {attribute}')
    message.set_purpose(Message_Purpose.FUNCTION_MESSAGE)
    message.set_target(Message_Purpose.CLIENT)
    message.set_function('fill_buffer')
    message.format_arguments(buffer_name, attribute)
    message.set_name(message.as_function())
    await send_to_client(server, client, message)


async def send_clients_to_console(server, target_consoles: (str, list) = None) -> None:
    """
    Send all currently connected clients to a particular console or a list of consoles
    :param server: reference to server calling the function
    :param target_consoles: (str) or (list) name of consoles to send to
    :return: Void
    """
    if isinstance(target_consoles, str):
        target_consoles = [target_consoles]

    if not target_consoles:
        target_consoles = list(server.consoles)

    clients = server.clients
    clients = {k: {k2: v2 for k2, v2 in v.items() if k2 != 'Socket'} for k, v in clients.items()}

    server.logger.debug(f'sending (clients) to console: {target_consoles}')
    for console in target_consoles:
        message = m.FunctionMessage(f'send_clients_to_console()')
        message.set_target(Message_Purpose.CONSOLE)
        message.set_function('set_clients')
        message.format_arguments(data=clients)
        await send_to_console(server, console, message)


async def send_attribute_to_console(server, attribute: str, buffer_name: str, target_consoles: (str, list) = None) -> None:
    """
        Sends the value of any attribute on the server object to any client
        :param server: reference to server calling the function
        :param attribute: (str) name of attribute to send
        :param buffer_name: (str) name of buffer on console you want to fill
        :param target_consoles: (str) | (list) of console names
        :return: Void
        """
    if isinstance(target_consoles, str):
        target_consoles = [target_consoles]

    if not target_consoles:
        target_consoles = list(server.consoles)

    server.logger.debug(f'sending ({attribute}) to console: {target_consoles}')
    attribute = getattr(server, attribute)
    message = m.FunctionMessage(f'set server name')
    message.set_purpose(Message_Purpose.FUNCTION_MESSAGE)
    message.set_target(Message_Purpose.CONSOLE)
    message.set_function('fill_buffer')
    message.format_arguments(buffer_name, attribute)
    message.set_name(message.as_function())
    for console in target_consoles:
        await send_to_console(server, console, message)


async def send_to_consoles(server, message: (m.Message, m.FunctionMessage)) -> None:
    """
    sends a message to every console connected to the server
    :param server: a reference to the server object calling
    :param message: (networkUtils.message.Message) | (networkUtils.message.FunctionMessage)
    :return: Void
    """
    for console in server.consoles:
        try:
            await send_to_console(server, console, message)
        except KeyError:
            continue


async def send_to_clients(server, clients: list, message: (m.Message, m.FunctionMessage)) -> None:
    """
    sends a message to every client connected to the server
    :param server: reference to the server making the function call
    :param clients: list of client names to send message to
    :param message: (networkUtils.message.Message) | (networkUtils.message.FunctionMessage)
    :return: Void
    """
    for client in clients:
        await send_to_client(server, client, message)


async def stop_client(server, client: str, hold_until: bool = False) -> None:
    new_message = m.FunctionMessage(f'Stop_Working -> {client}')
    new_message.set_target(Message_Purpose.CLIENT)
    new_message.set_function('stop_working')
    new_message.format_arguments(hold_until)

    await send_to_client(server, client, new_message)


async def update_client_attribute(server, client: str, attribute_name: str, attribute_value: any) -> None:
    """
    updates any client_attribute with any value
    :param server: reference to the server making the call
    :param client: client which is being updated
    :param attribute_name: name of attribute to update
    :param attribute_value: value to update to
    :return: Void
    """
    server.clients[client][attribute_name] = attribute_value


async def mark_task_as_finished(server, task_id: int) -> None:
    """
    Marks a task as finished in the scheduler
    :param server: reference to the server making the call
    :param task_id: task ID to mark as finished
    :return: Void
    """
    new_message = m.FunctionMessage('mark_task_as_finished()')
    new_message.set_target(Message_Purpose.CONSOLE)
    new_message.set_function('mark_task_as_finished')
    new_message.format_arguments(task_id)
    await send_to_consoles(server, new_message)
    await server.job_scheduler.finish_task(task_id)


async def mark_job_as_finished(server, job_id: int, from_console: bool = False) -> None:
    new_message = m.FunctionMessage('mark_job_as_finished()')
    new_message.set_target(Message_Purpose.CONSOLE)
    new_message.set_function('mark_job_as_finished')
    new_message.format_arguments(job_id)
    await send_to_consoles(server, new_message)
    await server.job_scheduler.finish_job(job_id, stop_workers=from_console)


async def mark_allocation_as_finished(server, allocation_id: int, from_console: bool = False) -> None:
    """
    Marks an allocation of tasks as finished in the scheduler
    :param server: Reference to the server making the call
    :param allocation_id: Allocation ID to mark as finished
    :param from_console: (bool) specifies if this function is a command from the console or just an envy instance reporting its completion
    :return: Void
    """
    new_message = m.FunctionMessage('mark_allocation_as_finished()')
    new_message.set_target(Message_Purpose.CONSOLE)
    new_message.set_function('mark_allocation_as_finished')
    new_message.format_arguments(allocation_id)
    await send_to_consoles(server, new_message)
    await server.job_scheduler.finish_allocation(allocation_id, stop_workers=from_console)

async def mark_allocation_as_started(server, allocation_id: int, computer: str) -> None:
    new_message = m.FunctionMessage('mark_allocation_as_started()')
    new_message.set_target(Message_Purpose.CONSOLE)
    new_message.set_function('mark_allocation_as_started')
    new_message.format_arguments(allocation_id, computer)
    await send_to_consoles(server, new_message)

async def mark_task_as_started(server, task_id: int, computer: str) -> None:
    """
    Marks a task as started in the scheduler
    :param server: Reference to the server making the call
    :param task_id: ID of the task to mark as started
    :param computer: name of the computer starting the task
    :return: Void
    """

    new_message = m.FunctionMessage('mark_task_as_started()')
    new_message.set_target(Message_Purpose.CONSOLE)
    new_message.set_function('mark_task_as_started')
    new_message.format_arguments(task_id, computer)
    await send_to_consoles(server, new_message)
    await server.job_scheduler.start_task(task_id, computer)

async def console_sync_job(server, job_id: int) -> None:
    new_message = m.FunctionMessage('console_sync_job()')
    new_message.set_target(Message_Purpose.CONSOLE)
    new_message.set_function('sync_job')
    new_message.format_arguments(job_id)
    await send_to_consoles(server, new_message)

async def console_register_client(server, client: str, client_data: dict) -> None:
    new_message = m.FunctionMessage(f'console_register_client() {client}')
    new_message.set_target(Message_Purpose.CONSOLE)
    new_message.set_function('register_client')
    new_message.format_arguments(client, data=client_data)
    await send_to_consoles(server, new_message)

async def console_unregister_client(server, client: str) -> None:
    new_message = m.FunctionMessage(f'console_register_client() {client}')
    new_message.set_target(Message_Purpose.CONSOLE)
    new_message.set_function('unregister_client')
    new_message.format_arguments(client)
    await send_to_consoles(server, new_message)

async def mark_task_as_failed(server, task_id: int, reason: str) -> None:
    new_message = m.FunctionMessage('mark_task_as_failed()')
    new_message.set_target(Message_Purpose.CONSOLE)
    new_message.set_function('mark_task_as_failed')
    new_message.format_arguments(task_id, reason)
    await send_to_consoles(server, new_message)
    await server.job_scheduler.fail_task(task_id, reason)

async def update_task_progress(server, task_id: int, progress: float) -> None:
    new_message = m.FunctionMessage('update_task_progress()')
    new_message.set_target(Message_Purpose.CONSOLE)
    new_message.set_function('update_task_progress')
    new_message.format_arguments(task_id, progress)
    await send_to_consoles(server, new_message)