import asyncio
import user_config, sys, os
sys.path.append(user_config.Config.REPOPATH)
sys.path.append(os.path.join(user_config.Config.ENVYPATH, 'Plugins'))
from networkUtils import message as m
from networkUtils.purpose import Purpose
from envyLib.colors import Colors as c
import json


async def debug(envy) -> None:
    """
    a generic debug function feel free to change this to whatever you want it to do
    called from console with debug_envy()
    :param envy: reference to the envy instance calling the function
    :return: Void
    """
    print(f'{c.IMPORTANT}Debug{c.CLEAR}')


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
    repopath = user_config.Config.REPOPATH
    os.startfile(f"launch_envy.py", cwd=str(repopath))
    quit()


async def send_status_to_server(envy) -> None:
    new_message = m.FunctionMessage('send_status_to_server()')
    new_message.set_function('update_client_attribute')
    new_message.format_arguments(envy.hostname, 'Status', envy.status)
    envy.send(new_message)


async def send_progress_to_server(envy, progress: float) -> None:
    new_message = m.FunctionMessage('send_task_progress_to_server()')
    new_message.set_function('update_client_attribute')
    new_message.format_arguments(envy.hostname, 'Progress', progress)
    envy.send(new_message)


async def finish_task(envy, task_id: int) -> None:
    new_message = m.FunctionMessage(f'finish_task(): {task_id}')
    new_message.set_target(Purpose.SERVER)
    new_message.set_function('mark_task_as_finished')
    new_message.format_arguments(task_id)
    envy.send(new_message)


async def debug_plugin(envy, task_data: str) -> None:
    from debug import envy_plugin as ep
    await envy.set_status_working()  # This is important to make sure that envy doesnt try to do other jobs

    task_data = json.loads(task_data)
    task_id = task_data['ID']
    environment = task_data['Environment']
    parameters = task_data['Parameters']
    frame = task_data['Frame']

    debug_process = ep.Debug(envy, task_id, frame)
    await debug_process.run()
    await envy.set_status_idle()
