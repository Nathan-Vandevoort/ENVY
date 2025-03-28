# -*- coding: utf-8 -*-

"""
Console_Functions.py: A "standard library" for Envy functions.
Any function written in here can be executed by any console
All functions in here must be async
the first argument in every function MUST be a reference to the console instance calling the function even if you don't use it.
Check out EXAMPLE to see how to write your own functions
feel free to use any of the existing functions as a template to build your own!
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.12"

import logging

from envy.lib.core.console.core import Console
from envy.lib.network import message as m
from envy.lib.network.message import MessageTarget, MessageType, FunctionMessage
from envy.lib.utils import utils as eutils

logger = logging.getLogger(__name__)


async def debug(console: Console) -> None:
    logger.info('WAHOOOOOOOOOO')


async def get_state(console: Console, client: str = None) -> None:
    if not client:
        client = await console.input('Which client:')
    new_message = FunctionMessage(f'Get state: {client}')
    new_message.set_target(MessageTarget.CLIENT)


async def CONSOLE_EXAMPLE(console: Console, arg1: int = None) -> None:
    """
    An example function to show users how to write their own console functions
    anything you write in here is executed by the console I recommend not requiring arguments and instead having the user pass them in with inputs
    These functions are commonly used to tell envy instances to do something. But they can be used to have the console do something instead.

    :param console: IMPORTANT first argument MUST be a reference to the console making the call even if you don't use it
    :param arg1: An example of how you can have arguments optionally supplied when calling the function or supply with inputs
    :return: Void
    """

    if arg1 is None:
        arg1 = input(f'What should Arg1 be (int)?')

        try:
            arg1 = int(arg1)
        except Exception as e:
            console.display_error(f'Arg1 MUST be an integer: -> {e}')
            return

    arg2 = input(f'What should Arg2 be (str)?')

    classifier = await get_classifier(console)
    valid = eutils.validate_classifier(classifier)
    if not valid:
        console.display_error(f'Invalid classifier: {classifier}')
        return

    new_message = m.FunctionMessage('EXAMPLE()')
    new_message.set_target(MessageTarget.CLIENT)
    new_message.set_function('ENVY_EXAMPLE')
    new_message.format_arguments(arg1, arg2=arg2)

    await send_to_clients(console, classifier, new_message)
    # notice how in the above function we passed in our current console. That's because ALL functions in Console_Functions.py need a reference to the current console even if it's not used


async def fill_buffer(console, buffer_name: str, data: any) -> None:
    """
    fills a buffer on the console given the buffers name and data to fill the buffer with
    :param console: reference to the console calling the function
    :param buffer_name: (str) name of buffer
    :param data: (any) data to fill buffer with
    :return: Void
    """
    setattr(console, buffer_name, data)


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


async def print_clients(console) -> None:
    console.display_info(console.clients_buffer)


async def sign_out(console) -> None:
    """
    Has envy sign out
    :param console: Reference to the console making the call
    :return: Void
    """
    classifier = await get_classifier(console)
    valid = eutils.validate_classifier(classifier)
    if not valid:
        console.display_error(f'Invalid classifier: {classifier}')
        return
    function_message = m.FunctionMessage('sign_out()')
    function_message.set_target(MessageTarget.CLIENT)
    function_message.set_function('sign_out')
    await send_to_clients(console, classifier, function_message)


async def request_clients(console) -> None:
    """
    Sends a message to the server requesting all the servers currently connected clients
    :param console: a reference to the console making the call
    :return: Void
    """
    function_message = m.FunctionMessage('request clients')
    function_message.set_target(MessageTarget.SERVER)
    function_message.set_function('send_clients_to_console')
    function_message.format_arguments(target_consoles=console.hostname)
    console.send(function_message)


async def restart_envy(console, force=False) -> None:
    """
    restart envy instances
    :param console: reference to the console making the call
    :param force: Bypasses the console prompting the user for a classifier
    :return: Void
    """
    if force == False:
        classifier = await get_classifier(console)
        valid = eutils.validate_classifier(classifier)
        if not valid:
            console.display_error(f'Invalid classifier: {classifier}')
            return
    else:
        classifier = '*'
    function_message = m.FunctionMessage('restart_envy()')
    function_message.set_target(MessageTarget.CLIENT)
    function_message.set_function('restart_envy')
    await send_to_clients(console, classifier, function_message)


async def get_classifier(console):
    console.display_info('Classifier (What computers to affect)?')
    classifier = await console.next_input(f"UserInput: ")
    return classifier


async def debug_envy(console) -> None:
    """
    has envy run its example function
    :param console: reference to the console calling this function
    :return: Void
    """
    classifier = get_classifier(console)
    valid = eutils.validate_classifier(classifier)
    if not valid:
        console.display_error(f'Invalid classifier: {classifier}')
        return
    function_message = m.FunctionMessage('debug_envy()')
    function_message.set_target(MessageTarget.CLIENT)
    function_message.set_function('example')
    await send_to_clients(console, classifier, function_message)


async def send_to_clients(console, classifier: str, function_message: m.FunctionMessage) -> None:
    """
    sends a single message to the server with a message.FunctionMessage within.
    the server will then send copies of the function message to any clients which meet the classifier
    :param console: reference to console making the call
    :param classifier: (str) classifier
    :param function_message: (network.message.FunctionMessage) A properly created FunctionMessage
    :return: Void
    """
    message = m.Message(f'Pass on: {function_message}')
    message.set_type(MessageType.PASS_ON)
    message.set_data(function_message.as_dict())
    message.set_message(classifier)
    console.send(message)


async def register_client(console, client: str, data: dict) -> None:
    console.clients_buffer[client] = data
    if console.console_widget is None:
        return
    console.console_widget.register_client.emit((client, data))


async def unregister_client(console, client: str) -> None:
    del console.clients_buffer[client]
    if console.console_widget is None:
        return
    console.console_widget.unregister_client.emit(client)


async def set_clients(console, data: dict) -> None:
    console.clients_buffer = data
    if console.console_widget is None:
        return
    console.console_widget.set_clients.emit(data)


async def version_mismatch(console, item_name: str, path_to_source: str, path_to_target: str) -> bool:
    import os
    import shutil

    # sanitize path to target
    sanitized = False
    target_file_type = None
    if os.path.isfile(path_to_target):
        sanitized = True
        target_file_type = 'file'

    if os.path.isdir(path_to_target):
        sanitized = True
        target_file_type = 'dir'

    if sanitized is False:
        console.display_error(f'{path_to_target} does not appear to be a valid file or directory')
        return False

    # sanitize path to source
    sanitized = False
    source_file_type = None
    if os.path.isfile(path_to_source):
        sanitized = True
        source_file_type = 'file'

    if os.path.isdir(path_to_source):
        sanitized = True
        source_file_type = 'dir'

    if sanitized is False:
        console.display_error(f'{path_to_source} does not appear to be a valid file or directory')
        return False

    if target_file_type != source_file_type:
        console.display_error(f'path_to_target and path_to_source must both be either a file or a directory not one of each')
        return False

    if console.console_widget is None:
        console.display_error(
            f'{item_name} version is mismatched from source. Would you like to update? (If you have customized {item_name} You will need to reimplement your customizations.)'
        )
        result = input('Confirm (y/n)')
        result = result.rstrip().upper()
        if result == 'Y':
            if target_file_type == 'file':
                if os.path.exists(path_to_target):
                    os.remove(path_to_target)
                try:
                    shutil.copy2(path_to_source, os.path.join(path_to_target, os.path.pardir))
                except Exception as e:
                    console.logger.error(f'Failed to pull {item_name} from source -> {e}')
                    return False

            if target_file_type == 'dir':
                if os.path.exists(path_to_target):
                    shutil.rmtree(path_to_target)
                try:
                    shutil.copytree(path_to_source, path_to_target)
                except Exception as e:
                    console.logger.error(f'Failed to pull {item_name} from source -> {e}')
                    return False
            return True
        else:
            console.display_info(f'Bypassing Update for {item_name}')
            return False

    else:
        reply = console.console_widget.show_confirmation(
            f'{item_name} version is mismatched from source.\nWould you like to update?\n(If you have customized {item_name} You will need to reimplement your customizations.)\nYou may need to reopen the console'
        )
        if reply is True:
            if target_file_type == 'file':
                if os.path.exists(path_to_target):
                    os.remove(path_to_target)
                shutil.copy2(path_to_source, os.path.join(path_to_target, os.path.pardir))

            if target_file_type == 'dir':
                if os.path.exists(path_to_target):
                    shutil.rmtree(path_to_target)
                shutil.copytree(path_to_source, path_to_target)
            return True
        else:
            console.display_info(f'Bypassing Update for {item_name}')
            return False


async def check_for_updates(console) -> None:
    console.check_plugin_versions()
    console.check_function_versions()


# ------------------------------ UI ---------------------------------------------- #
async def mark_job_as_finished(console, job_id: int) -> None:
    if console.console_widget is None:
        return
    console.console_widget.jobs_finish_job.emit(float(job_id))


async def mark_allocation_as_finished(console, allocation_id: int) -> None:
    if console.console_widget is None:
        return
    console.console_widget.jobs_finish_allocation.emit(float(allocation_id))


async def mark_allocation_as_started(console, allocation_id: int, computer: str) -> None:
    if console.console_widget is None:
        return
    console.console_widget.jobs_start_allocation.emit((allocation_id, computer))


async def mark_task_as_finished(console, task_id: int) -> None:
    if console.console_widget is None:
        return
    console.console_widget.jobs_finish_task.emit(float(task_id))


async def mark_task_as_started(console, task_id: int, computer: str) -> None:
    if console.console_widget is None:
        return
    console.console_widget.jobs_start_task.emit((task_id, computer))


async def sync_job(console, job_id: int) -> None:
    if console.console_widget is None:
        return
    console.console_widget.jobs_sync_job.emit(float(job_id))


async def mark_task_as_failed(console, task_id: int, reason: str) -> None:
    if console.console_widget is None:
        return
    console.console_widget.jobs_fail_task.emit((task_id, reason))


async def mark_allocation_as_failed(console, allocation_id: int, reason: str) -> None:
    if console.console_widget is None:
        return
    console.console_widget.jobs_fail_allocation.emit((allocation_id, reason))


async def update_allocation_progress(console, allocation_id: int, progress: int) -> None:
    if console.console_widget is None:
        return
    console.console_widget.jobs_update_allocation_progress.emit((allocation_id, progress))
