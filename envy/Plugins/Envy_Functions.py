import json
import dataclasses

from envy.lib.core.client.core import Client
from envy.lib.network import message as m
from envy.lib.network.message import MessageTarget


async def send_state(envy: Client) -> None:
    """Sends the current state of the envy instance to the server."""
    state = envy.state()
    state_dict = dataclasses.asdict(state)

    new_message = m.FunctionMessage(f'send_state')
    new_message.set_target(MessageTarget.SERVER)
    new_message.set_function('update_client_state')
    new_message.format_arguments(state=state_dict)

    envy.send(new_message)


async def finish_task(envy: Client, task_id: int) -> None:
    """
    Tells the server I'm done with the given task
    """
    new_message = m.FunctionMessage(f'finish_task(): {task_id}')
    new_message.set_target(MessageTarget.SERVER)
    new_message.set_function('mark_task_as_finished')
    new_message.format_arguments(task_id)
    envy.send(new_message)


async def finish_task_allocation(envy, allocation_id: int) -> None:
    """
    Tells the server I'm done with the group of tasks you gave me
    """
    new_message = m.FunctionMessage(f'finish_task_allocation(): {allocation_id}')
    new_message.set_target(MessageTarget.SERVER)
    new_message.set_function('mark_allocation_as_finished')
    new_message.format_arguments(allocation_id)
    envy.send(new_message)


async def start_task(envy, task_id: int) -> None:
    """
    Tells the server I just started this task
    :param envy: reference to the envy instance making the call
    :param task_id: ID of the task to mark as started
    :return: Void
    """
    new_message = m.FunctionMessage(f'start_task(): {task_id}')
    new_message.set_target(MessageTarget.SERVER)
    new_message.set_function('mark_task_as_started')
    new_message.format_arguments(task_id, envy.hostname)
    envy.send(new_message)


async def dirty_task(envy, task_id: int, reason: str = '') -> None:
    """
    This is here for legacy purposes It just points to fail_task
    :param envy: reference to the envy instance making the call
    :param task_id: The task ID to mark as failed
    :param reason: The reason why the task failed
    :return: Void
    """
    await fail_task(envy, task_id, reason=reason)


async def fail_task(envy, task_id: int, reason: str) -> None:
    """
    Allows plugins to mark a task as failed if something went wrong
    :param envy: reference to the envy instance calling the function
    :param task_id: The ID of the task to mark as failed
    :param reason: the reason why the task failed
    :return: Void
    """
    new_message = m.FunctionMessage(f'fail_task(): {task_id}')
    new_message.set_target(MessageTarget.SERVER)
    new_message.set_function('mark_task_as_failed')
    new_message.format_arguments(task_id, reason)
    envy.send(new_message)


async def fail_task_allocation(envy, allocation_id: int, reason: str) -> None:
    """
    Mark's an allocation as failed and supplies a reason
    :param envy: reference to the envy instance calling the function
    :param allocation_id: The ID of the allocation to mark as failed
    :param reason: The reason why the allocation failed
    :return: Void
    """
    new_message = m.FunctionMessage(f'fail_allocation(): {allocation_id}')
    new_message.set_target(MessageTarget.SERVER)
    new_message.set_function('mark_allocation_as_failed')
    new_message.format_arguments(allocation_id, reason)
    envy.send(new_message)


async def send_allocation_progress(envy, allocation_id: int, progress: int) -> None:
    """
    Reports the progress of a given allocation to the server.
    When using this function be careful that you don't flood the server with progress updates.
    :param envy: reference to the envy instance calling the function
    :param allocation_id: The ID of the allocation to update the progress on
    :param progress: The new progress
    :return:
    """
    new_message = m.FunctionMessage(f'send_allocation_progress(): {allocation_id}')
    new_message.set_target(MessageTarget.SERVER)
    new_message.set_function('update_allocation_progress')
    new_message.format_arguments(allocation_id, progress)
    envy.send(new_message)


async def PLUGIN_eHoudini(envy, allocation_data_string: str) -> None:
    """
    The Houdini plugin. Allows for caching and rendering through Houdini.
    :param envy: Reference to envy instance making the call
    :param allocation_data_string: The allocation data provided by the Scheduler as a json string
    :return: Void
    """
    from eHoudini import plugin as p

    await envy.set_status_working()
    envy.logger.info("eHoudini: Started")
    plugin = p.Plugin(envy, allocation_data_string)
    await plugin.start()
    await envy.set_status_idle()
    envy.logger.info("eHoudini: Exited")


async def PLUGIN_eMaya(envy, allocation_data: str) -> None:
    """"""
    from eMaya import maya_render

    await envy.set_status_working()
    envy.logger.info('eMaya: Started')
    allocation_data = json.loads(allocation_data)
    allocation_id = allocation_data['Allocation_Id']
    plugin = maya_render.MayaRender(envy, allocation_data)
    await plugin.render()
    await finish_task_allocation(envy, allocation_id)
    await envy.set_status_idle()
    envy.logger.info("eMaya: Exited")
