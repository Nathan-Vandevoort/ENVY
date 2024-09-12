# -*- coding: utf-8 -*-

"""
example.envy_plugin.py: The part of the plugin which controls managing the called process
There are some things to keep in mind when writing your own plugins
    1. Plugins are intended to call a separate process and provide the interface for envy to communicate with that process
    2. Plugins are given an allocation of tasks when called. This is a dictionary called tasks that looks kind of like this:
        {'Tasks', {'Task_ID_01': Frame #}, {'Task_ID_02': Frame #}, {'Task_ID_03': Frame #}, {'Task_ID_04': Frame #}}
    3. Your plugin MUST not block the existing envy asyncio event loop. Read the code below to see how I do this
    4. Your plugin MUST ensure that if envy were to be terminated any subprocesses you call are also terminated
    5. When the allocation of tasks is finished you MUST run Envy_Functions.finish_allocation() to ensure the scheduler knows that you successfully finished the allocation
    6. Your plugin MUST include an asynchronous task which monitors if envy.status changes from working and if so causes your plugin to exit gracefully
        This is to ensure that if a stop working signal is sent to envy it can safely shut down any processes its running
    7. If you want to report progress I highly recommend setting up some sort of progress buffer system where you send progress every x number of seconds only if the progress has changed.
        This stops the server from getting overloaded with a ton of realtime progress updates.
        Progress is for the entire allocation of frames NOT per frame. This means if you have 5 frames when the first frame finishes you are 20% done with your allocation.
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"

import os, subprocess
import asyncio
from envyRepo.envyJobs.enums import Status  # this module is in the ENVYREPO and provides useful information such as job status
import sys
import json
import time
NV = sys.modules.get('Envy_Functions')  # This gets the Envy_Functions module and assigns it to the variable NV. This allows you to call the envy_functions functions easily


class Example_Plugin_Handler:

    def __init__(self, envy, allocation_data: dict):
        """
        The initializing function for the Example_Plugin_Handler object.
        :param envy: I pass in a reference to the calling envy instance, so I can monitor envy.status and run Envy_Functions
        :param task_id: I accept the task id because I will need it to report the task has been finished later
        :param frame: I accept the frame just to show that you can have any arguments you want
        """

        self.process = None

        """
        The process I'm calling is relative to my current file location.
        Either hard code the path to whatever executable you will be calling OR better yet add it to the user config file. and read it in from there
        """

        self.my_path = os.path.abspath(__file__)
        self.allocation_id = allocation_data['Allocation_Id']
        self.tasks = allocation_data['Tasks']
        self.task_ids = list(self.tasks)
        self.number_of_tasks = len(self.task_ids)
        self.envy = envy
        self.coroutines = []
        self.progress_buffer = 0

    async def start_subprocess(self) -> None:
        """
        This method starts the given subprocess. In this case my test_process.py
        However for your use case you will probably be calling something like render.exe or vrayCommandLine.exe
        :return: Void
        """
        plugin_path = os.path.join(os.path.dirname(self.my_path), 'test_process.py')
        self.process = await asyncio.create_subprocess_exec(f'python',  plugin_path, json.dumps(self.tasks), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)  # notice how I'm using asyncios create subprocess and not the subprocess modules

    async def monitor_subprocess_output(self) -> int:
        """
        This coroutine monitors the stdout of the process I'm calling and reports back percentages
        :return: Void
        """
        async for line in self.process.stdout:  # because I'm using asyncio's create subprocess method I can iterate over the stdout with an async for loop. This is important to not block envy
            await self.parse_line(line)
        return await self.process.wait()

    async def monitor_envy(self) -> int:
        """
        This coroutine monitors envy for any change in envy.status. If the status changes from working then it will shutdown the plugin and its subprocess
        :return: (int) an exit code. Honestly I didn't finish implimenting this so the exit code is not used.
        """
        while self.envy.status == Status.WORKING:
            await asyncio.sleep(.5)  # this sleep is important. If you have never used asyncio before the `await asyncio.sleep` ensures that the while loop is not blocking
        return -1

    async def send_progress(self) -> None:
        """
        This coroutine will send updated progress to the server every 2 seconds.
        This avoids flooding the server with progress updates.
        :return: Void
        """
        last_progress = self.progress_buffer
        while True:
            await asyncio.sleep(2)
            if self.progress_buffer == last_progress:
                continue
            if len(self.task_ids) > 0:
                await NV.send_allocation_progress(self.envy, self.allocation_id, self.progress_buffer)
            last_progress = self.progress_buffer

    async def monitor_coroutines(self) -> None:
        """
        This coroutine will monitor the other coroutines without blocking the event loop. If any of the coroutines exit, this coroutine will clean up other coroutines and terminate the process.
        :return: Void
        """
        running = True
        while running:
            await asyncio.sleep(.01)
            for task in self.coroutines:
                if task.done():
                    self.envy.logger.debug(f'Example Plugin: termination catalyst task -> {task.get_name()}')
                    await self.end_coroutines()
                    self.terminate_process()
                    running = False
                    break

    async def end_coroutines(self):
        self.envy.logger.debug(f'Example Plugin: Ending coroutines')
        for task in self.coroutines:
            task.cancel()

    def terminate_process(self, timeout: float = 5):
        """
        sends a termination signal to the process and waits for timeout number of seconds until the process is closed
        :param timeout: how long to keep trying to terminate the process
        :return: (Bool) if the process was terminated successfully or not
        """
        self.envy.logger.info('Example Plugin: Terminating process')
        if self.process is None:
            return True

        start_time = time.time()
        while self.process.returncode is None:
            time.sleep(.1)
            if time.time() - start_time > timeout:
                return False
            self.process.terminate()
        return True

    async def parse_line(self, line):
        """
        The function which parses the lines from the stdout and decides what to do with them
        :param line:
        :return: Void
        """
        line = line.decode().rstrip()

        if '%' in line:
            percentage = float(line[:-1])
            completed_tasks = self.number_of_tasks - len(self.task_ids)
            completed_task_progress = (completed_tasks / self.number_of_tasks) * 100
            current_task_progress = percentage * (1 / self.number_of_tasks)
            self.envy.logger.info(f'Example Plugin: completed task progress {completed_task_progress} - current task progress {current_task_progress}')
            self.progress_buffer = int(completed_task_progress + current_task_progress)

        if 'FINISHED' in line:
            await NV.finish_task(self.envy, self.task_ids.pop(0))  # this tells the scheduler that it successfully finished the task
            if len(self.task_ids) > 0:  # make sure that there is a new task to start
                await NV.start_task(self.envy, self.task_ids[0])  # I assume that when a task is finished the next task is automatically started

    async def run(self):
        """
        The function which actually starts plugin
        :return: Void
        """
        await self.start_subprocess()
        await NV.start_task(self.envy, self.task_ids[0])  # I assume that when I launch the process I start the first task

        monitor_subprocess_task = self.envy.event_loop.create_task(self.monitor_subprocess_output())
        monitor_subprocess_task.set_name('monitor_subprocess_output()')
        self.coroutines.append(monitor_subprocess_task)

        monitor_envy_task = self.envy.event_loop.create_task(self.monitor_envy())
        monitor_envy_task.set_name('monitor_envy()')
        self.coroutines.append(monitor_envy_task)

        send_progress_task = self.envy.event_loop.create_task(self.send_progress())
        send_progress_task.set_name('send_progress()')
        self.coroutines.append(send_progress_task)

        await self.monitor_coroutines()  # hold here until one of the coroutines exits

        if self.process.returncode == 0:  # if the process exists cleanly then mark the allocation as finished
            await NV.finish_task_allocation(self.envy, self.allocation_id)
        else:  # if the process exited with an error code give the console the error code and mark the allocation as failed
            await NV.fail_task_allocation(self.envy, self.allocation_id, str(self.process.returncode))

