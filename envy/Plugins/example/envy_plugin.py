# -*- coding: utf-8 -*-

"""
example.envy_plugin.py: The part of the plugin which controls managing the called process
There are some things to keep in mind when writing your own plugins
    1. Plugins are intended to call a separate process and provide the interface for envy to communicate with that process
    2. Plugins are given a Task when they are called. and tasks are issued by the job scheduler. It is up to you how you use the given task information
    3. Your plugin MUST not block the existing envy asyncio event loop. Read the code below to see how I do this
    4. Your plugin MUST ensure that if envy were to be terminated any subprocesses you call are also terminated
    5. When the task is finished you MUST run Envy_Functions.finish_task() to ensure the scheduler knows that you successfully finished the task
    6. Your plugin MUST include an asynchronous task which monitors if envy.status changes from working and if so causes your plugin to exit gracefully
        This is to ensure that if a stop working signal is sent to envy it can safely shut down any processes its running
"""

__author__ = "Nathan Vandevoort"
__copyright__ = "Copyright 2024, Nathan Vandevoort"
__version__ = "1.0.0"

import os, subprocess
import asyncio
from envyJobs.enums import Status  # this module is in the ENVYREPO and provides useful information such as job status
import sys
import json
NV = sys.modules.get('Envy_Functions')  # This gets the Envy_Functions module and assigns it to the variable NV. This allows you to call the envy_functions functions easily


class Example_Plugin_Handler:

    def __init__(self, envy, tasks: dict):
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

        self.tasks = tasks
        self.task_ids = list(tasks)
        self.envy = envy

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
        This process monitors the stdout of the process I'm calling and reports back percentages
        :return: Void
        """
        async for line in self.process.stdout:  # because I'm using asyncio's create subprocess method I can iterate over the stdout with an async for loop. This is important to not block envy
            await self.parse_line(line)
        return await self.process.wait()

    async def monitor_envy(self) -> int:
        """
        This process monitors envy for any change in envy.status. If the status changes from working then it will shutdown the plugin and its subprocess
        :return: (int) an exit code. Honestly I didn't finish implimenting this so the exit code is not used.
        """
        while self.envy.status == Status.WORKING:
            await asyncio.sleep(.5)  # this sleep is important. If you have never used asyncio before the await asyncio.sleep ensures that the while loop is not blocking
        return -1

    async def parse_line(self, line):
        """
        The function which parses the lines from the stdout and decides what to do with them
        :param line:
        :return: Void
        """
        line = line.decode().rstrip()
        print(line)

        if '%' in line:
            percentage = float(line[:-1])
            #await NV.send_progress_to_server(self.envy, percentage)

        if 'FINISHED' in line:
            await NV.finish_task(self.envy, self.task_ids.pop(0))  # this tells the scheduler that it succesfully finished the task
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
        monitor_subprocess_task.set_name('Plugin-Example_Plugin_Handler: monitor_subprocess_output()')
        monitor_envy_task = self.envy.event_loop.create_task(self.monitor_envy())
        monitor_envy_task.set_name('Plugin-Example_Plugin_Handler: monitor_envy()')
        done, pending = await asyncio.wait(
            [monitor_envy_task, monitor_subprocess_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()  # this cleans up other running tasks if one of them finished
        self.process = None
