import os, subprocess
import asyncio
from envyJobs.enums import Status
import sys
import time
NV = sys.modules.get('Envy_Functions')  # get user defined Envy_Functions as NV


class Debug:

    def __init__(self, envy, task_id: int, frame: int):
        self.process = None
        self.my_path = os.path.abspath(__file__)
        self.envy = envy
        self.task_id = task_id
        self.frame = frame
        self.envy.logger.info(f'Plugin-Debug: Initialized -> Frame: {frame}')

    async def start_subprocess(self):
        plugin_path = os.path.join(os.path.dirname(self.my_path), 'test_process.py')
        cmd = ['python', plugin_path]
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
        self.process = await asyncio.create_subprocess_shell(f'python {plugin_path}', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    async def monitor_subprocess_output(self) -> int:
        async for line in self.process.stdout:
            await self.parse_line(line)
        return await self.process.wait()

    async def monitor_envy(self) -> int:
        while self.envy.status == Status.WORKING:
            await asyncio.sleep(.5)
        return -1

    async def parse_line(self, line):
        line = line.decode().rstrip()

        if '%' in line:
            percentage = float(line[:-1])
            await NV.send_progress_to_server(self.envy, percentage)

    async def run(self):
        await self.start_subprocess()
        monitor_subprocess_task = self.envy.event_loop.create_task(self.monitor_subprocess_output())
        monitor_subprocess_task.set_name('Plugin-Debug: monitor_subprocess_output()')
        monitor_envy_task = self.envy.event_loop.create_task(self.monitor_envy())
        monitor_envy_task.set_name('Plugin-Debug: monitor_envy()')
        done, pending = await asyncio.wait(
            [monitor_envy_task, monitor_subprocess_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        self.process = None
        await NV.finish_task(self.envy, self.task_id)


if __name__ == '__main__':
    async def test():
        plugin_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_process.py')
        cmd = ['python', plugin_path]
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NEW_CONSOLE
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creation_flags)

        for message in process.stdout:
            print(message)

    asyncio.run(test())