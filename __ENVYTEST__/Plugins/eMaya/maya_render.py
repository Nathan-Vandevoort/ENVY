"""
========================================================================================================================
Name: maya_render.py
========================================================================================================================
"""
import asyncio
import json
import sys
import re
import os

from envyJobs.enums import Status

NV = sys.modules.get('Envy_Functions')


class MayaRender(object):
    ARNOLD = 'arnold'
    REDSHIFT = 'redshift'
    VRAY = 'vray'

    MAYA_RENDER_EXE_PATH = 'C:/Program Files/Autodesk/Maya2024/bin/Render.exe'

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
        self.maya_file_modification_time = 0

        self.current_frame = 1
        self.current_layer = 1
        self.progress = 0
        
        self.render_subprocess = None


        self.vray_is_rendering = False

    @staticmethod
    def check_settings_keys(settings: dict) -> bool:
        """Checks the settings dictionary keys."""
        print(settings)

        expected_keys = [
            'maya_file',
            'project_path',
            'maya_version',
            'render_engine',
            'camera',
            'render_layer',
            'maya_file_modification_time'
        ]

        actual_keys = set(settings.keys())
        expected_keys_set = set(expected_keys)

        return actual_keys == expected_keys_set

    def get_settings_from_json(self) -> bool:
        """Gets the settings from json."""
        if not self.check_settings_keys(settings=self.environment):
            self.logger.error('Settings are not valid.')
            return False

        self.set_maya_file(self.environment['maya_file'])
        self.set_project(self.environment['project_path'])
        self.set_render_engine(self.environment['render_engine'])
        self.set_start_frame(next(iter(self.tasks.items()))[-1])
        self.set_end_frame(next(iter(self.tasks.items()))[-1])

        self.camera = self.environment['camera']
        self.render_layer = self.environment['render_layer']
        self.maya_version = self.environment['maya_version']
        self.maya_file_modification_time = self.environment['maya_file_modification_time']

        self.logger.info('Settings read successfully.')

        return True

    def is_maya_file_valid(self, maya_file: str) -> bool:
        """Checks if the maya file exists."""
        if not maya_file:
            self.logger.error('Maya file has not been set.')
            # TODO: finish envy
            return False
        elif not os.path.exists(maya_file):
            self.logger.error('Maya file does not exists.')
            return False
        else:
            return True

    def is_project_path_valid(self, project_path: str) -> bool:
        """Checks if the project exists."""
        if not project_path:
            self.logger.error('Project path has not been set.')
            return False
        elif not os.path.exists(project_path):
            self.logger.error('Project path does not exists.')
            return False
        else:
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

        return -1

    async def calculate_render_progress(self, progress: int) -> None:
        """Calculates and print the render progress such as the current frame, layer."""
        if progress < self.progress:
            if self.current_frame > self.end_frame:
                self.current_frame = self.start_frame
                self.current_layer += 1

                if len(self.task_list) > 0:
                    await NV.finish_task(self.envy, self.task_list.pop(0))

                if len(self.task_list) > 0:
                    await NV.start_task(self.envy, self.task_list[0])

        self.progress = progress

        await NV.send_task_progress(self.envy, float(self.progress))

        self.logger.info(
            f'Frame: {self.current_frame} '
            f'Layer: {self.render_layer} '
            f'Progress: {self.progress}%')

    async def print_render_progress(self):
        """Prints the render progress."""
        while True:
            log_line = await self.render_subprocess.stdout.readline()

            if log_line:
                log_line = log_line.decode().strip()
                self.envy.logger.debug(log_line)
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
                    self.logger.info(log_line)
            else:
                break

    async def monitor_envy(self) -> int:
        """"""
        while self.envy.status == Status.WORKING:
            await asyncio.sleep(.5)
        return -1

    async def monitor_process(self):
        """Monitors the render process."""
        while True:
            await self.print_render_progress()
            await asyncio.sleep(5)
            if self.render_subprocess.returncode is not None:
                break

    async def render(self) -> None:
        self.envy.logger.info(f'eMaya: render started')
        """Renders the Maya file."""
        if not self.get_settings_from_json():
            return
        elif not self.is_maya_file_valid(self.maya_file):
            return
        elif not self.is_project_path_valid(self.project_path):
            return
        elif not self.render_engine:
            self.logger.error('Render engine has not been set.')
            return
        elif self.render_engine == 'invalid':
            self.logger.error('Render engine not supported.')
            return
        elif self.maya_file_modification_time != os.path.getmtime(self.maya_file):
            self.logger.error('Maya file has been modified.')
            return

        self.logger.info('Starting render.')

        self.current_frame = self.start_frame

        await self.start_render_subprocess()

        await NV.start_task(self.envy, self.task_list[0])
        monitor_subprocess_task = self.envy.event_loop.create_task(self.monitor_process())
        monitor_subprocess_task.set_name('maya_render_task')
        monitor_envy_task = self.envy.event_loop.create_task(self.monitor_envy())
        monitor_envy_task.set_name('maya_render_envy_task')
        done, pending = await asyncio.wait(
            [monitor_envy_task, monitor_subprocess_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()

        exit_code = await self.render_subprocess.wait()

        if exit_code == 0:
            self.logger.info('eMaya: Render completed.')
            asyncio.run(NV.finish_task_allocation(self.envy, self.allocation_id))
        else:
            asyncio.run(NV.dirty_task_allocation(self.envy, self.allocation_id))  # todo change finish task to dirty task
            self.logger.error(f'eMaya: Render failed. Error {exit_code}.')

        self.envy.logger.info(f'eMaya: render ended')
    def set_maya_file(self, maya_file: str) -> None:
        """Sets the maya file."""
        if not self.is_maya_file_valid(maya_file=maya_file):
            self.envy.logger.info(f'eMaya: set_maya_file Fail')
            return

        self.maya_file = maya_file
        self.envy.logger.info(f'eMaya: set_maya_file Success')

    def set_project(self, project_path: str) -> None:
        """Sets the Maya project."""
        if not self.is_project_path_valid(project_path=project_path):
            self.envy.logger.info(f'eMaya: set_project Fail')
            return

        self.project_path = project_path
        self.envy.logger.info(f'eMaya: set_project Success')

    def set_render_engine(self, render_engine: str) -> None:
        """Sets the render engine."""
        if render_engine == MayaRender.ARNOLD:
            self.render_engine = render_engine
        elif render_engine == MayaRender.REDSHIFT:
            self.render_engine = render_engine
        elif render_engine == MayaRender.VRAY:
            self.render_engine = render_engine
        else:
            self.render_engine = 'invalid'
        self.envy.logger.info(f'eMaya: set_render_engine {self.render_engine}')

    def set_end_frame(self, end_frame: int) -> None:
        """Sets the end frame."""
        if not isinstance(end_frame, (int, float)):
            self.logger.error('End frame must be an int value.')
            return

        self.end_frame = int(end_frame)

        if self.end_frame < self.start_frame:
            self.start_frame = self.end_frame
        self.envy.logger.info(f'eMaya: set_end_frame {end_frame}')

    def set_start_frame(self, start_frame: int) -> None:
        """Sets the start frame."""
        if not isinstance(start_frame, (int, float)):
            self.logger.error('Start frame must be an int value.')
            return

        self.start_frame = int(start_frame)

        if self.start_frame > self.end_frame:
            self.end_frame = self.start_frame
        self.envy.logger.info(f'eMaya: set_start_frame = {start_frame}')

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
        self.envy.logger.info(f'eMaya: start_render_subprocess: {command}')
        self.render_subprocess = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
