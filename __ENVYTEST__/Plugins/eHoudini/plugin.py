"""
eHoudini.plugin.py: the handler for the houdini process
"""
import asyncio
import sys
import os
import atexit
import psutil
import time
c = sys.modules.get('__config__').Config
NV = sys.modules.get('Envy_Functions')


class Plugin:

    def __init__(self, envy, task_id, environment: dict, parameters: dict):
        self.envy = envy
        self.task_id = task_id
        self.environment = environment
        self.parameters = parameters
        self.logger = self.envy.logger

        self.hython_process = None
        self.ready_to_write = False

        atexit.register(self.exit_function)

    async def start_process(self):
        plugin_path = os.path.join(c.HOUDINIBINPATH, 'hython.exe')
        proc = await asyncio.create_subprocess_shell(f'{plugin_path}', stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        self.logger.info(f'eHoudini: Started process hython_process')
        return proc

    async def start(self) -> None:
        self.hython_process = await self.start_process()
        # todo remember to have parameter edits happen AFTER the advanced edits

    async def terminate_process(self, timeout: float = 5) -> bool:
        if self.hython_process is None:
            return True

        start_time = time.time()
        while self.hython_process.poll is None:
            await asyncio.sleep(.05)
            if time.time() - start_time > timeout:
                return False
            self.hython_process.terminate()
        return True

    async def monitor_output(self):
        async for line in self.hython_process.stdout:
            await self.parse_line(line)
        return await self.hython_process.wait()

    async def parse_line(self, line: bytes) -> None:
        line = line.decode()

        if '>>>' in line:  # ready for input
            self.ready_to_write = True
            return

    async def write_to_hython(self, message: str, wait: bool = True) -> None:
        if wait:
            # Wait for new line
            while not self.ready_to_write:
                await asyncio.sleep(.1)

        self.write(message)
        self.logger.debug(f'eHoudini: to hython -> {message}')

    def write(self, message: str):
        message += '\n'
        self.hython_process.stdin.write(message)

    def exit_function(self) -> None:
        self.logger.info('eHoudini: exit function called')
        self.logger.info('eHoudini: Terminating child process')
        success = self.terminate_process()
        if not success:
            self.logger.error(f'eHoudini: FAILED TO TERMINATE CHILD PROCESS')
        self.logger.info(f'eHoudini: terminated child process')
        self.logger.info(f'eHoudini: successfully closed')