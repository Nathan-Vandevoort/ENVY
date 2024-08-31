"""
========================================================================================================================
Name: maya_render.py
========================================================================================================================
"""
import asyncio
import sys
import re
import os

from envyJobs.enums import Status

config = sys.modules.get('config_bridge').Config
NV = sys.modules.get('Envy_Functions')


class MayaRender(object):
    PLUGIN_NAME = 'eMaya'

    ARNOLD = 'arnold'
    REDSHIFT = 'redshift'
    VRAY = 'vray'

    MAYA_RENDER_EXE_PATH = os.path.join(config.MAYABINPATH, 'Render.exe')

    def __init__(self, envy, allocation_data: dict):
        """"""
        self.envy = envy
        self.event_loop = envy.event_loop
        self.allocation_id = allocation_data['Allocation_Id']
        self.logger = envy.logger
        self.tasks = allocation_data['Tasks']
        self.task_list = list(self.tasks)
        self.environment = allocation_data['Environment']

        self.maya_file = None
        self.project_path = None
        self.maya_version = 0
        self.render_engine = None
        self.camera = None
        self.render_layer = None
        self.start_frame = 1
        self.end_frame = 1

        self.current_frame = 1
        self.current_layer = 1
        self.progress = 0

        self.render_subprocess = None
        self.vray_is_rendering = False

    @staticmethod
    def check_settings_keys(settings: dict) -> bool:
        """Checks the settings dictionary keys."""
        expected_keys = [
            'maya_file',
            'project_path',
            'maya_version',
            'render_engine',
            'camera',
            'render_layer',
        ]

        actual_keys = set(settings.keys())
        expected_keys_set = set(expected_keys)

        return actual_keys == expected_keys_set

    def get_settings_from_data_base(self) -> bool:
        """Gets the settings from json."""
        if not self.check_settings_keys(settings=self.environment):
            self.logger.error(f'{MayaRender.PLUGIN_NAME}: Settings are invalid.\n{self.environment}')
            return False

        frames = list(self.tasks.values())

        self.set_maya_file(self.environment['maya_file'])
        self.set_project(self.environment['project_path'])
        self.set_render_engine(self.environment['render_engine'])
        self.set_start_frame(frames[0])
        self.set_end_frame(frames[-1])

        self.camera = self.environment['camera']
        self.render_layer = self.environment['render_layer']
        self.maya_version = self.environment['maya_version']

        self.logger.info(f'{MayaRender.PLUGIN_NAME}: Settings from data base read successfully.')

        return True

    def is_maya_file_valid(self, maya_file: str) -> bool:
        """Checks if the maya file exists."""
        if not maya_file:
            self.logger.error(f'{MayaRender.PLUGIN_NAME}: Maya file has not been set.')
            return False
        elif not os.path.exists(maya_file):
            self.logger.error(f'{MayaRender.PLUGIN_NAME}: Maya file does not exists.')
            return False
        elif not maya_file.startswith('Z:/'):
            self.logger.error(f'{MayaRender.PLUGIN_NAME}: Maya file must be saved on the Z:/ drive.')
            return False
        else:
            return True

    def is_project_path_valid(self, project_path: str) -> bool:
        """Checks if the project exists."""
        if not project_path:
            self.logger.error(f'{MayaRender.PLUGIN_NAME}: Project path has not been set.')
            return False
        elif not os.path.exists(project_path):
            self.logger.error(f'{MayaRender.PLUGIN_NAME}: Project path does not exists.')
            return False
        elif not project_path.startswith('Z:/'):
            self.logger.error(f'{MayaRender.PLUGIN_NAME}: Project path must be set on the Z:/ drive.')
            return False
        else:
            return True

    def is_render_engine_valid(self) -> bool:
        """Checks if the render engine is supported."""
        if not self.render_engine:
            self.logger.error(f'{MayaRender.PLUGIN_NAME}: Render engine has not been set.')
            return False

        return True

    @staticmethod
    async def get_arnold_render_progress(log_line: str) -> int:
        """Gets the Arnold render progress."""
        pattern = r'(\d+)\s*%'
        match = re.search(pattern, log_line)

        if match:
            percentage = match.group(1)
            return int(percentage)

        return -101

    @staticmethod
    async def get_redshift_render_progress(log_line: str) -> int:
        """Gets the Redshift render progress."""
        pattern = r'Block (\d+/\d+) \(\d+,\d+\) rendered by GPU \d+ in \d+ms'
        match = re.search(pattern, log_line)

        if match:
            percentage = match.group(1)
            fraction, divisor = percentage.split('/')

            return int((int(fraction) / int(divisor)) * 100)

        return -102

    async def get_vray_render_progress(self, log_line: str) -> int:
        """Gets the V-Ray render progress."""
        if 'Rendering image... (finished in' in log_line:
            self.vray_is_rendering = False
        elif 'Rendering image...' in log_line:
            self.vray_is_rendering = True

        if self.vray_is_rendering:
            pattern = r'(\d+)\s*%'
            match = re.search(pattern, log_line)

            if match:
                percentage = match.group(1)
                return int(percentage)

        return -103

    async def get_render_progress(self, log_line: str) -> int:
        """Gets the render progress."""
        if self.render_engine == MayaRender.ARNOLD:
            return await self.get_arnold_render_progress(log_line=log_line)
        elif self.render_engine == MayaRender.VRAY:
            return await self.get_vray_render_progress(log_line=log_line)
        elif self.render_engine == MayaRender.REDSHIFT:
            return await self.get_redshift_render_progress(log_line=log_line)
        else:
            return -1

    async def calculate_render_progress(self, progress: int) -> None:
        """Calculates and print the render progress such as the current frame, layer."""
        if progress < self.progress:
            if self.current_frame > self.end_frame:
                self.current_frame = self.start_frame
                self.current_layer += 1

        self.progress = progress

        if len(self.task_list) > 0:
            await NV.send_task_progress(self.envy, self.task_list[0], float(self.progress))

        if self.progress == 100:
            if len(self.task_list) > 0:
                await NV.finish_task(self.envy, self.task_list.pop(0))

            if len(self.task_list) > 0:
                await NV.start_task(self.envy, self.task_list[0])

        self.logger.info(
            f'{MayaRender.PLUGIN_NAME}: '
            f'Layer: {self.render_layer} | '
            f'Camera: {self.camera} | '
            f'Frame: {self.current_frame} | '
            f'Progress: {self.progress}%')

    async def monitor_render_progress(self):
        """Monitors the render progress."""
        while True:
            log_line = await self.render_subprocess.stdout.readline()

            if log_line:
                log_line = log_line.decode().strip()
                self.envy.logger.debug(f'eMaya: {log_line}')

                if self.render_engine == MayaRender.ARNOLD:
                    if '% done' in log_line:
                        progress = await self.get_render_progress(log_line=log_line)

                        if progress > 0:
                            await self.calculate_render_progress(progress=progress)

                elif self.render_engine == MayaRender.VRAY:
                    progress = await self.get_render_progress(log_line=log_line)

                    if progress > 0:
                        await self.calculate_render_progress(progress=progress)

                elif self.render_engine == MayaRender.REDSHIFT:
                    if 'Block ' in log_line:
                        progress = await self.get_render_progress(log_line=log_line)

                        if progress > 0:
                            await self.calculate_render_progress(progress=progress)
                else:
                    self.logger.info(f'eMaya: {log_line}')
            else:
                break

    async def monitor_envy(self) -> int:
        """Monitors Envy."""
        while self.envy.status == Status.WORKING:
            await asyncio.sleep(.5)

        return -1

    async def monitor_process(self):
        """Monitors the render process."""
        while True:
            await self.monitor_render_progress()
            await asyncio.sleep(5)
            if self.render_subprocess.returncode is not None:
                break

    async def monitor_tasks(self):
        running = True
        while running:
            await asyncio.sleep(.01)
            for task in self.coroutines:
                if task.done():
                    self.logger.debug(f'eMaya: task {task.get_name()}')
                    await self.end_coroutines()
                    running = False

    async def render(self) -> None:
        """Renders the Maya file."""
        self.envy.logger.info(f'{MayaRender.PLUGIN_NAME}: Launching {MayaRender.PLUGIN_NAME}.')

        if not self.get_settings_from_data_base():
            return
        elif not self.is_maya_file_valid(self.maya_file):
            return
        elif not self.is_project_path_valid(self.project_path):
            return
        elif not self.is_render_engine_valid():
            return

        self.logger.info(f'{MayaRender.PLUGIN_NAME}: Validations completed.')

        self.current_frame = self.start_frame

        await self.start_render_subprocess()

        await NV.start_task(self.envy, self.task_list[0])

        monitor_subprocess_task = self.envy.event_loop.create_task(self.monitor_process())
        monitor_subprocess_task.set_name('maya_render_task')
        monitor_envy_task = self.envy.event_loop.create_task(self.monitor_envy())
        monitor_envy_task.set_name('maya_render_envy_task')

        # await self.monitor_tasks()

        exit_code = await self.render_subprocess.wait()

        if exit_code == 0:
            await NV.finish_task_allocation(self.envy, self.allocation_id)
            self.logger.info(f'{MayaRender.PLUGIN_NAME}: Render completed.')
        else:
            await NV.dirty_task_allocation(self.envy, self.allocation_id)
            self.logger.error(f'{MayaRender.PLUGIN_NAME}: Render failed. Error {exit_code}.')

        self.envy.logger.info(f'{MayaRender.PLUGIN_NAME}: Closing {MayaRender.PLUGIN_NAME}.')

    def set_maya_file(self, maya_file: str) -> None:
        """Sets the maya file."""
        if not self.is_maya_file_valid(maya_file=maya_file):
            self.envy.logger.info(f'{MayaRender.PLUGIN_NAME}: Set Maya file failed.')
            return

        self.maya_file = maya_file
        self.envy.logger.info(f'{MayaRender.PLUGIN_NAME}: Set Maya file to {self.maya_file}.')

    def set_project(self, project_path: str) -> None:
        """Sets the Maya project."""
        if not self.is_project_path_valid(project_path=project_path):
            self.envy.logger.info(f'{MayaRender.PLUGIN_NAME}: Set project failed.')
            return

        self.project_path = project_path
        self.envy.logger.info(f'{MayaRender.PLUGIN_NAME}: Set project to {self.project_path}.')

    def set_render_engine(self, render_engine: str) -> None:
        """Sets the render engine."""
        if render_engine in [MayaRender.ARNOLD, MayaRender.REDSHIFT, MayaRender.VRAY]:
            self.render_engine = render_engine
        else:
            self.render_engine = None
            self.logger.error(f'{MayaRender.PLUGIN_NAME}: {render_engine} render engine is not supported.')

    def set_end_frame(self, end_frame: int) -> None:
        """Sets the end frame."""
        if not isinstance(end_frame, (int, float)):
            self.logger.error(f'{MayaRender.PLUGIN_NAME}: End frame must be an int value.')
            return

        self.end_frame = int(end_frame)

        if self.end_frame < self.start_frame:
            self.start_frame = self.end_frame
        self.envy.logger.info(f'{MayaRender.PLUGIN_NAME}: Set end frame to {end_frame}.')

    def set_start_frame(self, start_frame: int) -> None:
        """Sets the start frame."""
        if not isinstance(start_frame, (int, float)):
            self.logger.error(f'{MayaRender.PLUGIN_NAME}: Start frame must be an int value.')
            return

        self.start_frame = int(start_frame)

        if self.start_frame > self.end_frame:
            self.end_frame = self.start_frame

        self.envy.logger.info(f'{MayaRender.PLUGIN_NAME}: Set start frame to {start_frame}.')

    async def start_render_subprocess(self) -> None:
        """Stats the render subprocess."""
        command = [
            MayaRender.MAYA_RENDER_EXE_PATH,
            '-cam', self.camera,
            '-rl', self.render_layer,
            '-s', str(self.start_frame),
            '-e', str(self.end_frame),
            '-proj', self.project_path,
            self.maya_file]

        self.envy.logger.info(f'{MayaRender.PLUGIN_NAME}: Starting render subprocess: {command}')

        self.render_subprocess = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)