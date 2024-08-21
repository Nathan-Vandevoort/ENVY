"""
eHoudini.plugin.py: the handler for the houdini process
"""
import asyncio
import os
import atexit
import subprocess
import time
import sys
import pty

from envyJobs.enums import Status as Job_Status
c = sys.modules.get('__config__').Config
NV = sys.modules.get('Envy_Functions')


class Plugin:

    def __init__(self, envy, allocation_data: dict):

        purpose = allocation_data['Purpose']

        self.envy = envy
        self.event_loop = envy.event_loop
        self.tasks = allocation_data['Tasks']
        self.task_list = list(self.tasks)
        self.environment = allocation_data['Environment']
        self.parameters = allocation_data['Parameters']

        targetButtonNode = self.environment['Target_Button']
        targetButtonNodeSplit = targetButtonNode.split('/')
        self.targetButtonParmName = targetButtonNodeSplit.pop()
        self.targetButtonNode = '/'.join(targetButtonNodeSplit)

        self.logger = self.envy.logger

        self.hython_process = None
        self.ready_to_write = False

        self.coroutines = []

        atexit.register(self.exit_function)

    async def start_process(self):
        plugin_path = os.path.join(c.HOUDINIBINPATH, 'hython.exe')
        proc = await asyncio.create_subprocess_exec(plugin_path, '-i', stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, creationflags=subprocess.CREATE_NEW_CONSOLE)
        self.logger.info(f'eHoudini: Started process hython_process')
        return proc

    async def start(self) -> None:
        self.hython_process = await self.start_process()

        monitor_output_task = self.event_loop.create_task(self.monitor_output())
        monitor_output_task.set_name('monitor_output()')
        self.coroutines.append(monitor_output_task)

        monitor_envy_task = self.event_loop.create_task(self.monitor_envy())
        monitor_envy_task.set_name('monitor_envy()')
        self.coroutines.append(monitor_envy_task)

        await self.houdini_load_hip_file()
        await self.houdini_set_parameter_changes()
        await self.houdini_press_cache_button()

        done, pending = await asyncio.wait(
            [monitor_envy_task, monitor_output_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()  # this cleans up other running tasks if one of them finished

    async def houdini_load_hip_file(self):
        await self.write_to_hython(f"hou.putenv('JOB', '{self.environment['JOB']}')")
        self.logger.info('eHoudini: set project')
        await self.write_to_hython((f"hou.hipFile.load('{self.environment['HIP']}')"))
        self.logger.info('eHoudini: opened hipfile')

    async def houdini_set_parameter_changes(self):
        for parm in self.parameters:
            # Isolate node
            parmSplit = parm.split('/')
            parmName = parmSplit.pop()
            parmNode = '/'.join(parmSplit)
            await self.write_to_hython(f"parmNode = hou.node('{parmNode}')")

            # Isolate Parm and set value
            value = self.parameters[parm]

            # add quotes to value
            value = f"'{str(value)}'"

            # set the value of the parm
            await self.write_to_hython(f"targetParm = parmNode.parm('{parmName}')")
            await self.write_to_hython(f"targetParm.setExpression({value}, language=hou.exprLanguage.Hscript)")
            await self.write_to_hython(f"targetParm.pressButton()")
            self.logger.info(f'eHoudini: Set parameter {parmName} on {parmNode} to {value}')

    async def houdini_press_cache_button(self):
        await self.write_to_hython(f"targetNode = hou.node('{self.targetButtonNode}')")
        await self.write_to_hython(f"targetParm = targetNode.parm('{self.targetButtonParmName}')")
        await self.write_to_hython(f"targetParm.pressButton()")
        self.logger.info('eHoudini: pressed start button')

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

    async def parse_line(self, line: bytes) -> bool:
        print(line)
        if b'>>>' == line:  # ready for input
            self.ready_to_write = True
            print('detected')
            return True
        return False
        if '%' in line:
            return True

        if 'FINISHED' in line:
            await NV.finish_task(self.envy, self.task_list.pop(0))
            if len(self.task_list) > 0:
                await NV.start_task(self.envy, self.task_list[0])
            return True
        return False

    async def write_to_hython(self, message: str, wait: bool = True) -> None:
        if wait:
            # Wait for new line
            while self.ready_to_write is False:
                await asyncio.sleep(.1)

        await self.write(message)

    async def monitor_envy(self) -> int:
        async for line in self.hython_process.stderr:
            print(line)
        while self.envy.status == Job_Status.WORKING:
            await asyncio.sleep(.5)
        return -1

    async def write(self, message: str):
        message += '\n'
        self.hython_process.stdin.write(message.encode())
        await self.hython_process.stdin.drain()
        self.logger.info(f'eHoudini: to hython -> {message}')
        self.ready_to_write = False

    def exit_function(self) -> None:
        self.logger.info('eHoudini: exit function called')
        self.logger.info('eHoudini: Terminating child process')
        success = self.terminate_process()
        if not success:
            self.logger.error(f'eHoudini: FAILED TO TERMINATE CHILD PROCESS')
        self.logger.info(f'eHoudini: terminated child process')
        self.logger.info(f'eHoudini: successfully closed')

if __name__ == '__main__':
    async def run_command():
        # Create a pseudo-terminal
        master_fd, slave_fd = pty.openpty()

        process = await asyncio.create_subprocess_exec(
            'hython', '-i',  # Use the -i flag for interactive mode
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=asyncio.subprocess.PIPE
        )

        async def send_input(input_data):
            try:
                os.write(master_fd, input_data.encode() + b'\n')
                print("Input sent successfully")
            except Exception as e:
                print(f"Failed to send input: {e}")

        async def read_output():
            while True:
                output = await asyncio.get_event_loop().run_in_executor(None, os.read, master_fd, 1024)
                if output:
                    print(f'STDOUT: {output.decode()}', end='', flush=True)
                else:
                    break

        await send_input('initial_input')
        await asyncio.create_task(read_output())

        await asyncio.sleep(2)
        await send_input('next_input')

        await asyncio.sleep(2)
        await send_input('another_input')

        await process.wait()

        # Close the pseudo-terminal
        os.close(master_fd)
        os.close(slave_fd)


    asyncio.run(run_command())