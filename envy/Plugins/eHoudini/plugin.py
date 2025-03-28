"""
eHoudini.plugin.py: the handler for the houdini process
"""

import asyncio
import os
import safe_exit
import subprocess
import time
import sys
import json
from envy.lib.jobs import Status as Job_Status
from envy.lib.utils import utils as eutils
import re

c = sys.modules.get('utils.config_bridge').Config
NV = sys.modules.get('Envy_Functions')


class Plugin:

    def __init__(self, envy, allocation_data_string: str):

        allocation_data = json.loads(allocation_data_string)
        self.allocation_data_string = allocation_data_string
        self.allocation_id = allocation_data['Allocation_Id']
        self.job_type = allocation_data['Environment']['Job_Type']
        self.envy = envy
        self.event_loop = envy.event_loop
        self.tasks = allocation_data['Tasks']
        self.task_list = list(self.tasks)
        self.number_of_tasks = len(self.task_list)
        self.logger = self.envy.logger
        self.hython_process = None
        self.coroutines = []
        self.ignore_counter = 0
        self.return_code = None
        self.user_terminated = False
        self.progress_buffer = 0

        self.failed = False
        self.fail_reason = r''
        safe_exit.register(self.exit_function)

        self.logger.debug(f'Allocation Data String: {allocation_data_string}')

    async def start_simulation_process(self):
        plugin_path = os.path.join(c.HOUDINIBINPATH, 'hython.exe')
        abs_file = os.path.abspath(__file__)
        file_dir = os.path.dirname(abs_file)
        fuck_windows = self.allocation_data_string.replace('"', "'")
        cmd = f'"{plugin_path}" -q "{os.path.join(file_dir, "simulation.py")}" "{fuck_windows}"'
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.logger.info(f'eHoudini: Started hython_process')
        return proc

    async def start_generic_process(self):
        plugin_path = os.path.join(c.HOUDINIBINPATH, 'hython.exe')
        abs_file = os.path.abspath(__file__)
        file_dir = os.path.dirname(abs_file)
        fuck_windows = self.allocation_data_string.replace('"', "'")
        cmd = f'"{plugin_path}" -q "{os.path.join(file_dir, "generic.py")}" "{fuck_windows}"'
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.logger.info(f'eHoudini: Started hython_process')
        return proc

    async def start_resumable_simulation_process(self):
        plugin_path = os.path.join(c.HOUDINIBINPATH, 'hython.exe')
        abs_file = os.path.abspath(__file__)
        file_dir = os.path.dirname(abs_file)
        fuck_windows = self.allocation_data_string.replace('"', "'")
        cmd = f'"{plugin_path}" -q "{os.path.join(file_dir, "resumable_simulation.py")}" "{fuck_windows}"'
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.logger.info(f'eHoudini: Started hython_process')
        return proc

    async def start_cache_process(self):
        plugin_path = os.path.join(c.HOUDINIBINPATH, 'hython.exe')
        abs_file = os.path.abspath(__file__)
        file_dir = os.path.dirname(abs_file)
        fuck_windows = self.allocation_data_string.replace('"', "'")
        cmd = f'"{plugin_path}" -q "{os.path.join(file_dir, "cache.py")}" "{fuck_windows}"'
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.logger.info(f'eHoudini: Started hython_process')
        return proc

    async def start(self) -> None:

        if self.number_of_tasks == 0:
            await NV.finish_task_allocation(self.envy, self.allocation_id)
            self.logger.warning(f'eHoudini: Allocation does not seem to have any tasks')
            return

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

        if len(self.task_list) > 0:
            await NV.start_task(self.envy, self.task_list[0])

        monitor_output_task = self.event_loop.create_task(self.monitor_output())
        monitor_output_task.set_name('monitor_output()')
        self.coroutines.append(monitor_output_task)

        monitor_error_task = self.event_loop.create_task(self.monitor_error())
        monitor_error_task.set_name('monitor_error()')
        self.coroutines.append(monitor_error_task)

        send_progress_task = self.event_loop.create_task(self.send_progress())
        send_progress_task.set_name('send_progress()')
        self.coroutines.append(send_progress_task)

        monitor_envy_task = self.event_loop.create_task(self.monitor_envy())
        monitor_envy_task.set_name('monitor_envy()')
        self.coroutines.append(monitor_envy_task)

        await self.monitor_tasks()

        while self.hython_process.returncode is None:
            await asyncio.sleep(0.1)

        self.logger.info(f'eHoudini: return code {self.hython_process.returncode}')

        if self.failed is True:
            await NV.fail_task_allocation(self.envy, self.allocation_id, self.fail_reason.strip())
            return

        if self.user_terminated is False:
            if self.hython_process.returncode == 0:
                await NV.finish_task_allocation(self.envy, self.allocation_id)
            else:
                await NV.fail_task_allocation(self.envy, self.allocation_id, str(self.hython_process.returncode))

    def terminate_process(self, timeout: float = 10) -> bool:
        self.logger.info('eHoudini: Terminating houdini process')
        if self.hython_process is None:
            return True

        start_time = time.time()
        while self.hython_process.returncode is None:
            time.sleep(0.1)
            if time.time() - start_time > timeout:
                return False
            self.hython_process.terminate()
        return True

    async def monitor_output(self):
        self.logger.info('eHoudini: Monitoring output')
        async for line in self.hython_process.stdout:
            await self.parse_line(line)
        self.return_code = self.hython_process.returncode
        return

    async def monitor_error(self):
        self.logger.info('eHoudini: Monitoring error')
        async for line in self.hython_process.stderr:
            has_error = await self.parse_line_error(line)
            line_sanitized = line.decode('unicode_escape', errors='ignore').strip()
            line_sanitized = re.sub(r'\\[nrt]]', '', line_sanitized)
            self.fail_reason += f' {line_sanitized}'
            if has_error is True and self.failed is False:
                self.failed = True
                fail_task = self.event_loop.create_task(self.fail_allocation())
                fail_task.set_name('fail_task()')
                self.coroutines.append(fail_task)

        self.return_code = self.hython_process.returncode
        return

    async def fail_allocation(self, timeout=1):
        for i in range(timeout):
            await asyncio.sleep(1)

    async def monitor_tasks(self):
        running = True
        while running:
            await asyncio.sleep(0.01)
            for task in self.coroutines:
                if task.done():
                    self.logger.debug(f'eHoudini: termination catalyst task -> {task.get_name()}')
                    await self.end_coroutines()
                    self.terminate_process()
                    running = False
                    break

    async def send_progress(self):
        last_progress = self.progress_buffer
        while True:
            await asyncio.sleep(2)
            if self.progress_buffer == last_progress:
                continue
            if len(self.task_list) > 0:
                await NV.send_allocation_progress(self.envy, self.allocation_id, self.progress_buffer)
            last_progress = self.progress_buffer

    async def end_coroutines(self):
        self.logger.debug(f'eHoudini: Ending coroutines')
        for task in self.coroutines:
            task.cancel()

    async def parse_line_error(self, line: bytes) -> bool:
        line = line.decode()
        line = line.strip()
        self.logger.error(f'eHoudini: {line}')
        if 'Render failed.' in line:
            return True
        return False

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
                self.ignore_counter = int(value) - 1

        if '%' in line:
            line_split = line.split()
            for token in line_split:
                if '%' not in token:
                    continue
                token = token[:-1]
                try:
                    progress = float(token)
                    self.progress_buffer = int(progress)
                except ValueError:
                    return True
            return True

        if 'FINISHED' in line:

            if self.ignore_counter > 0:
                self.ignore_counter -= 1
                self.logger.debug(f'Finished repeated frame')
                return True

            if len(self.task_list) > 0:
                await NV.finish_task(self.envy, self.task_list.pop(0))

            if len(self.task_list) > 0:
                await NV.start_task(self.envy, self.task_list[0])
            return True

        return False

    async def monitor_envy(self) -> int:
        while self.envy.status == Job_Status.WORKING:
            await asyncio.sleep(0.5)
        self.user_terminated = True
        return -1

    def exit_function(self) -> None:
        self.logger.info('eHoudini: exit function called')
        self.logger.info('eHoudini: Terminating child process')
        success = self.terminate_process()
        eutils.shutdown_event_loop(self.event_loop, logger=self.logger)
        if not success:
            self.logger.error(f'eHoudini: FAILED TO TERMINATE CHILD PROCESS')
        self.logger.info(f'eHoudini: terminated child process')
        self.logger.info(f'eHoudini: successfully closed')
