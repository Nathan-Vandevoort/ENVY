"""
eHoudini.plugin.py: the handler for the houdini process
"""
import asyncio
import os
import atexit
import subprocess
import time
import sys
import json
from envyJobs.enums import Status as Job_Status
c = sys.modules.get('config_bridge').Config
NV = sys.modules.get('Envy_Functions')


class Plugin:

    def __init__(self, envy, allocation_data_string: str):

        allocation_data = json.loads(allocation_data_string)
        self.allocation_data_string = allocation_data_string
        self.job_type = allocation_data['Environment']['Job_Type']
        self.envy = envy
        self.event_loop = envy.event_loop
        self.tasks = allocation_data['Tasks']
        self.task_list = list(self.tasks)
        self.logger = self.envy.logger
        self.hython_process = None
        self.coroutines = []
        self.ignore_counter = 0
        atexit.register(self.exit_function)

        self.logger.debug(f'Allocation Data String: {allocation_data_string}')

    async def start_simulation_process(self):
        plugin_path = os.path.join(c.HOUDINIBINPATH, 'hython.exe')
        abs_file = os.path.abspath(__file__)
        file_dir = os.path.dirname(abs_file)
        fuck_windows = self.allocation_data_string.replace('"', "'")
        cmd = f'"{plugin_path}" "{os.path.join(file_dir, "simulation.py")}" "{fuck_windows}"'
        proc = await asyncio.create_subprocess_shell(cmd, stdin=asyncio.subprocess.PIPE,
                                                     stdout=asyncio.subprocess.PIPE,
                                                     stderr=asyncio.subprocess.PIPE,
                                                     creationflags=subprocess.CREATE_NO_WINDOW
                                                     )
        self.logger.info(f'eHoudini: Started hython_process')
        return proc

    async def start_generic_process(self):
        plugin_path = os.path.join(c.HOUDINIBINPATH, 'hython.exe')
        abs_file = os.path.abspath(__file__)
        file_dir = os.path.dirname(abs_file)
        fuck_windows = self.allocation_data_string.replace('"', "'")
        cmd = f'"{plugin_path}" "{os.path.join(file_dir, "generic.py")}" "{fuck_windows}"'
        proc = await asyncio.create_subprocess_shell(cmd,
                                                     stdin=asyncio.subprocess.PIPE,
                                                     stdout=asyncio.subprocess.PIPE,
                                                     stderr=asyncio.subprocess.PIPE,
                                                     creationflags=subprocess.CREATE_NO_WINDOW
                                                     )
        self.logger.info(f'eHoudini: Started hython_process')
        return proc

    async def start_resumable_simulation_process(self):
        plugin_path = os.path.join(c.HOUDINIBINPATH, 'hython.exe')
        abs_file = os.path.abspath(__file__)
        file_dir = os.path.dirname(abs_file)
        fuck_windows = self.allocation_data_string.replace('"', "'")
        cmd = f'"{plugin_path}" "{os.path.join(file_dir, "resumable_simulation.py")}" "{fuck_windows}"'
        proc = await asyncio.create_subprocess_shell(cmd,
                                                     stdin=asyncio.subprocess.PIPE,
                                                     stdout=asyncio.subprocess.PIPE,
                                                     stderr=asyncio.subprocess.PIPE,
                                                     creationflags=subprocess.CREATE_NO_WINDOW
                                                     )
        self.logger.info(f'eHoudini: Started hython_process')
        return proc

    async def start_cache_process(self):
        plugin_path = os.path.join(c.HOUDINIBINPATH, 'hython.exe')
        abs_file = os.path.abspath(__file__)
        file_dir = os.path.dirname(abs_file)
        fuck_windows = self.allocation_data_string.replace('"', "'")
        cmd = f'"{plugin_path}" "{os.path.join(file_dir, "cache.py")}" "{fuck_windows}"'
        proc = await asyncio.create_subprocess_shell(cmd, stdin=asyncio.subprocess.PIPE,
                                                     stdout=asyncio.subprocess.PIPE,
                                                     stderr=asyncio.subprocess.PIPE,
                                                     creationflags=subprocess.CREATE_NO_WINDOW
                                                     )
        self.logger.info(f'eHoudini: Started hython_process')
        return proc

    async def start(self) -> None:
        if self.job_type == 'simulation':
            self.logger.debug('eHoudini: starting simulation process')
            self.hython_process = await self.start_simulation_process()

        if self.job_type == 'generic':
            self.logger.debug('eHoudini: starting generic process')
            self.hython_process = await self.start_generic_process()

        if self.job_type == 'cache':
            self.logger.debug('eHoudini: starting cache process')
            self.hython_process = await self.start_cache_process()

        if self.job_type == 'resumable_simulation':
            self.logger.debug('eHoudini: starting resumable simulation process')
            self.hython_process = await self.start_resumable_simulation_process()

        monitor_output_task = self.event_loop.create_task(self.monitor_output())
        monitor_output_task.set_name('monitor_output()')
        self.coroutines.append(monitor_output_task)

        monitor_error_task = self.event_loop.create_task(self.monitor_error())
        monitor_error_task.set_name('monitor_error()')
        self.coroutines.append(monitor_error_task)

        monitor_envy_task = self.event_loop.create_task(self.monitor_envy())
        monitor_envy_task.set_name('monitor_envy()')
        self.coroutines.append(monitor_envy_task)

        done, pending = await asyncio.wait(
            [monitor_envy_task, monitor_output_task, monitor_error_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in done:
            print(task)

        for task in pending:
            task.cancel()  # this cleans up other running tasks if one of them finished

    def terminate_process(self, timeout: float = 5) -> bool:
        if self.hython_process is None:
            return True

        start_time = time.time()
        while self.hython_process.poll is None:
            time.sleep(.1)
            if time.time() - start_time > timeout:
                return False
            self.hython_process.terminate()
        return True

    async def monitor_output(self):
        self.logger.info('eHoudini: Monitoring output')
        async for line in self.hython_process.stdout:
            await self.parse_line(line)
        return self.hython_process

    async def monitor_error(self):
        self.logger.info('eHoudini: Monitoring error')
        async for line in self.hython_process.stderr:
            await self.parse_line(line)
        return self.hython_process

    async def parse_line(self, line: bytes) -> bool:
        line = line.decode()
        line = line.strip()
        self.logger.debug(f'eHoudini: {line}')

        if '$ENVY:' in line:
            command = line.split(':')[1]
            command_split = command.split('=')
            command = command_split[0]
            value = command_split[1]

            if command == 'NEWSTARTFRAME':
                self.ignore_counter = int(value)

        if '%' in line:
            return True

        if 'FINISHED' in line:

            if self.ignore_counter > 0:
                self.ignore_counter -= 1
                return True

            if len(self.task_list) > 0:
                await NV.finish_task(self.envy, self.task_list.pop(0))

            if len(self.task_list) > 0:
                await NV.start_task(self.envy, self.task_list[0])
            return True

        return False

    async def monitor_envy(self) -> int:
        while self.envy.status == Job_Status.WORKING:
            await asyncio.sleep(.5)
        return -1

    def exit_function(self) -> None:
        self.logger.info('eHoudini: exit function called')
        self.logger.info('eHoudini: Terminating child process')
        success = self.terminate_process()
        if not success:
            self.logger.error(f'eHoudini: FAILED TO TERMINATE CHILD PROCESS')
        self.logger.info(f'eHoudini: terminated child process')
        self.logger.info(f'eHoudini: successfully closed')