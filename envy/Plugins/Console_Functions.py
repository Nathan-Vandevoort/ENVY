# -*- coding: utf-8 -*-

"""
Console_Functions.py: A "standard library" for Envy functions.
Any function written in here can be executed by any console
All functions in here must be async
the first argument in every function MUST be a reference to the console instance calling the function even if you dont use it.
Check out EXAMPLE to see how to write your own functions
feel free to use any of the existing functions as a template to build your own!
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"

from envyRepo.networkUtils import message as m
from envyRepo.networkUtils.message_purpose import Message_Purpose
from envyRepo.envyLib import envy_utils as eutils
from envyRepo.envyLib.colors import Colors as c
import shutil
import sys
import os
import json
__config__ = sys.modules.get('__config__')


async def CONSOLE_EXAMPLE(console, arg1: int = None) -> None:
    """
    An example function to show users how to write their own console functions
    anything you write in here is executed by the console I recommend not requiring arguments and instead having the user pass them in with inputs
    These functions are commonly used to tell envy instances to do something. But they can be used to have the console do something instead.

    :param console: IMPORTANT first argument MUST be a reference to the console making the call even if you don't use it
    :param arg1: An example of how you can have arguments optionally supplied when calling the function or supply with inputs
    :return: Void
    """

    if arg1 is None:  # Checks to see if arg1 is supplied during function call and if not prompt the user for arg1.
        arg1 = input(f'{c.CYAN}What should Arg1 be (int)?{c.WHITE}')  # prompting the user for arg1. Notice the colors which are stored in the ENVYREPO/envyLib/Colors

        try:  # Try to cast the argument to an integer
            arg1 = int(arg1)
        except Exception as e:  # if it's not the right type inform the user its wrong and return and print why it couldnt be casted to an int
            console.display_error(f'Arg1 MUST be an integer: -> {e}')
            return

    arg2 = input(f'{c.CYAN}What should Arg2 be (str)?{c.WHITE}')  # prompt the user for arg2. This argument cannot be passed in at call time because the function isn't expecting it as an argument

    classifier = await get_classifier(console)  # a convenience function which prompts the user for a classifier or "which computers should I send this message to" If you are sending this message to the server this is unnecessary
    valid = eutils.validate_classifier(classifier)  # a function within REPOPATH/envyLib/envy_utils.py which validates that the user supplied classifier is a valid classifier
    if not valid:  # if the classifier is not valid tell the user and return
        console.display_error(f'Invalid classifier: {classifier}')
        return

    new_message = m.FunctionMessage('EXAMPLE()')  # Create a new function message. A function message is the standard way to get envy (commonly referred to as client) or the server to do something.
    new_message.set_target(Message_Purpose.CLIENT)  # Setting the target is important. Think about it like putting an address on a letter. The server will only execute functions with the target set to SERVER and vice versa with clients
    new_message.set_function('ENVY_EXAMPLE')  # setting the function to the name of the function in Envy_Functions.py that we want to call
    new_message.format_arguments(arg1, arg2=arg2)  # You set the arguments for the functions in here. As if you were doing it while calling the function

    await send_to_clients(console, classifier, new_message)  # a convenience function which wraps the function message in a normal message and tells the server to pass on the function message to all clients who match the classifier
    # notice how in the above function we passed in our current console. Thats because ALL functions in Console_Functions.py need a reference to the current console even if its not used


async def fill_buffer(console, buffer_name: str, data: any) -> None:
    """
    fills a buffer on the console given the buffers name and data to fill the buffer with
    :param console: reference to the console calling the function
    :param buffer_name: (str) name of buffer
    :param data: (any) data to fill buffer with
    :return: Void
    """
    setattr(console, buffer_name, data)


async def install_maya_plugin(console) -> None:
    """
    installs the Maya plugin
    :param console: reference to the console calling the function
    """
    maya_user_folder = 'Z:/maya'
    envy_plugin_path = '__ENVYTEST__/Plugins/eMaya/envyCore.py'

    if not os.path.exists(maya_user_folder):
        console.display_error('Maya plugin installation failed: Maya user folder not found.')
        return
    elif not os.path.exists(envy_plugin_path):
        console.display_error('Maya plugin installation failed: Envy plugin not found.')
        return

    for folder in os.listdir(maya_user_folder):
        if folder.isdigit():
            maya_plugins_folder = os.path.join(maya_user_folder, folder, 'plug-ins')

            if not os.path.exists(maya_plugins_folder):
                os.mkdir(maya_plugins_folder)

            shutil.copy(envy_plugin_path, maya_plugins_folder)

    console.display_info('Maya plugin installed successfully.')


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
    function_message.set_target(Message_Purpose.CLIENT)
    function_message.set_function('sign_out')
    await send_to_clients(console, classifier, function_message)


async def request_clients(console) -> None:
    """
    Sends a message to the server requesting all the servers currently connected clients
    :param console: a reference to the console making the call
    :return: Void
    """
    function_message = m.FunctionMessage('request clients')
    function_message.set_target(Message_Purpose.SERVER)
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
    function_message.set_target(Message_Purpose.CLIENT)
    function_message.set_function('restart_envy')
    await send_to_clients(console, classifier, function_message)


async def get_classifier(console):
    console.display_info('Classifier (What computers to affect)?')
    classifier = await console.next_input(f"{c.CYAN}UserInput: {c.WHITE}")
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
    function_message.set_target(Message_Purpose.CLIENT)
    function_message.set_function('example')
    await send_to_clients(console, classifier, function_message)


async def send_to_clients(console, classifier: str, function_message: m.FunctionMessage) -> None:
    """
    sends a single message to the server with a message.FunctionMessage within.
    the server will then send copies of the function message to any clients which meet the classifier
    :param console: reference to console making the call
    :param classifier: (str) classifier
    :param function_message: (networkUtils.message.FunctionMessage) A properly created FunctionMessage
    :return: Void
    """
    message = m.Message(f'Pass on: {function_message}')
    message.set_purpose(Message_Purpose.PASS_ON)
    message.set_data(function_message.as_dict())
    message.set_message(classifier)
    console.send(message)


async def version(console) -> str:
    return '0.0.1'


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


async def version_mismatch(console, item_name: str, path_to_target: str, path_to_source: str) -> None:
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
        return

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
        return

    if target_file_type != source_file_type:
        console.display_error(f'path_to_target and path_to_source must both be either a file or a directory not one of each')
        return

    if console.console_widget is None:
        console.display_error(f'{item_name} version is mismatched from source. Would you like to update? (If you have customized {item_name} You will need to reimplement your customizations.)')
        result = input('Confirm (y/n)').rstrip().upper()
        if result == 'Y':
            if target_file_type == 'file':
                if os.path.exists(path_to_target):
                    os.remove(path_to_target)
                shutil.copy2(path_to_source, path_to_target)

            if target_file_type == 'dir':
                if os.path.exists(path_to_target):
                    shutil.rmtree(path_to_target)
                shutil.copytree(path_to_source, path_to_target)

        else:
            console.display_info('Bypassing Update')
            return