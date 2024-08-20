# -*- coding: utf-8 -*-

"""
Envy_Functions.py: A "standard library" for Envy functions.
Any function written in here can be executed by any envy instance
All functions in here must be async
the first argument in every function MUST be a reference to the envy instance calling the function even if you dont use it.
Check out the CONSOLE_EXAMPLE (Console_Functions.py) function to see how to write your own functions which can be called by envy.
Check out PLUGIN_EXAMPLE to see how to write your own plugins
feel free to use any of the existing functions as a template to build your own!
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"

from networkUtils import message as m
from networkUtils.message_purpose import Message_Purpose
import json, sys
from envyLib.colors import Colors as c
__config__ = sys.modules.get('__config__')


async def ENVY_EXAMPLE(envy, arg1: int, arg2: str = 'potato') -> None:
    """
    An example function which you can use as a template to write your own
    All functions MUST be async even if you don't use any asyncio things
    called from console with CONSOLE_EXAMPLE()
    If you want to see how to write plugins check out PLUGIN_EXAMPLE()
    :param envy: reference to the envy instance calling the function
    :param arg1: (int) number of times to print arg2
    :param arg2: (str) what gets printed
    :return: Void
    """
    for i in range(arg1):  # prints whatever arg2 is arg1 many times. this is just an example of what sort of stuff you can do. But look at more examples!
        print(arg2)


async def PLUGIN_EXAMPLE(envy, allocation_data: str) -> None:
    """
    A template on how you can implement your own plugins for envy.
    This is the "Handle" function for envy that any job I create is referencing as its Type: job.set_type('PLUGIN_EXAMPLE')
    :param envy: As always you MUST include a reference to the envy instance making the call
    :param allocation_data: (json string) This will ALWAYS be a json encoded string that will contain the Allocation_Id, Purpose, Tasks, Environment, Parameters
    :return: Void
    """
    from example import envy_plugin as ep  # Here I'm importing the plugin data I've written in my 'example' plugin library
    await envy.set_status_working()  # ALWAYS start a new plugin by setting the envy status to working. This tells the scheduler to not issue more tasks to this instance

    allocation_data = json.loads(allocation_data)  # converting task_data from a json string to a dictionary
    allocation_id = allocation_data['Allocation_Id']
    tasks = allocation_data['Tasks']  # allocation_data.tasks is ALWAYS a dictionary where the Key is the task ID (You can use this to tell the scheduler individual frames are done) and the Value is the frame to render
    environment = allocation_data['Environment']  # environment can contain whatever information you want. You encode this information into the job. I normally use it for scene file path / project path
    parameters = allocation_data['Parameters']  # This can also contain any arbitrary data you want

    debug_process = ep.Example_Plugin_Handler(envy, tasks)  # Here I'm initializing my example plugin. You can do this however you want. take a look inside /example/envy_plugin

    await debug_process.run()  # Here I'm starting my example plugin take a look inside /example/envy_plugin to learn more
    await finish_task_allocation(envy, allocation_id)  # Always end your plugin by finishing the assigned task allocation. If you do not the scheduler will not know that it is finished.
    await envy.set_status_idle()  # THIS IS IMPORTANT. when the plugin is done set the status to idle. This tells the scheduler that its okay to issue more jobs to this instance[


async def fill_buffer(envy, buffer_name: str, data: any) -> None:
    """
    fills a buffer on envy given the buffers name and data to fill the buffer with
    :param envy: reference to the envy instance calling the function
    :param buffer_name: (str) name of buffer
    :param data: (any) data to fill buffer with
    :return: Void
    """
    setattr(envy, buffer_name, data)


async def install_maya_plugin(envy) -> None:
    """
    installs the Maya plugin
    :param envy: reference to the envy instance calling the function
    """
    e_maya_path = '//titansrv/studentShare/nathanV/Envy_V2/ENVYTEST/Plugins/eMaya'
    user_maya_path = 'Z:/maya'

    """
    TODO: look for maya versions
    creates plugin folder if it does not exists
    check if there is the envy.py installed already, probably replace it so it could be updated all the time
    copy the envy.py file for each maya version in the user maya folder 
    """


async def restart_envy(envy) -> None:
    import os
    """
    launches a new envy instance and shuts down the current one
    :param envy: reference to the envy instance calling the function
    :return: Void
    """
    ENVYPATH = __config__.Config.ENVYPATH
    os.startfile(f"launch_envy.py", cwd=str(ENVYPATH))
    quit()


async def send_status_to_server(envy) -> None:
    """
    tells the server what my current Status is
    :param envy: reference to the envy instance calling the function
    :return: Void
    """
    new_message = m.FunctionMessage('send_status_to_server()')
    new_message.set_function('update_client_attribute')
    new_message.format_arguments(envy.hostname, 'Status', envy.status)
    envy.send(new_message)


async def finish_task(envy, task_id: int) -> None:
    """
    Tells the server I'm done with the given task
    :param envy: reference to envy instance calling function
    :param task_id: The Task_ID of the task to mark as finished
    :return: Void
    """
    new_message = m.FunctionMessage(f'finish_task(): {task_id}')
    new_message.set_target(Message_Purpose.SERVER)
    new_message.set_function('mark_task_as_finished')
    new_message.format_arguments(task_id)
    envy.send(new_message)


async def finish_task_allocation(envy, allocation_id: int) -> None:
    """
    Tells the server I'm done with the group of tasks you gave me
    :param envy: reference to envy instance making the call
    :param allocation_id: the Allocation_Id of the allocation to mark as finished
    :return: Void
    """
    new_message = m.FunctionMessage(f'finish_task_allocation(): {allocation_id}')
    new_message.set_target(Message_Purpose.SERVER)
    new_message.set_function('mark_allocation_as_finished')
    new_message.format_arguments(allocation_id)
    envy.send(new_message)


# ------------------------------------------------------------------------------------- PLUG-INS -------------------------------------------------------------------------------------
async def PLUGIN_eHoudini(envy, task_data: str) -> None:
    from eHoudini import plugin as p
    await envy.set_status_working()

    task_data = json.loads(task_data)
    purpose = task_data['Purpose']
    task_id = task_data['ID']
    environment = task_data['Environment']
    parameters = task_data['Parameters']
    frame = task_data['Frame']

    plugin = p.Plugin(envy, task_id, environment, parameters)
    await plugin.start()

