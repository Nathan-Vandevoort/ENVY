"""
========================================================================================================================
Name: maya_render.py
========================================================================================================================
"""
import asyncio
import logging
import json
import re
import os


class MayaRender(object):
    ARNOLD = 'arnold'
    REDSHIFT = 'redshift'
    VRAY = 'vray'

    RENDER_PROGRESS_PATTERNS = {
        ARNOLD: '% done',
        REDSHIFT: '',
        VRAY: ''
    }

    MAYA_RENDER_EXE_PATH = 'C:/Program Files/Autodesk/Maya2024/bin/Render.exe'
    MAYA_UTILS = 'Z:/eMaya/maya_to_envy.py'

    def __init__(self, event_loop, logger):
        """"""
        self.maya_file = None
        self.project_path = None
        self.maya_version = 2024
        self.render_engine = None
        self.render_layers = []
        self.start_frame = 1
        self.end_frame = 1
        self.maya_file_modification_time = -1

        self.current_frame = 0
        self.current_layer = 1
        self.progress = 0
        
        self.render_subprocess = None
        self.event_loop = event_loop
        self.logger = logger

    def get_settings_from_json(self, json_path: str) -> bool:
        """Gets the settings from json."""
        if not json_path:
            self.logger.error('JSON file does not exists.')
            return False
        if not os.path.exists(json_path):
            self.logger.error('JSON file does not exists.')
            return False

        self.logger.info(' Reading render settings from JSON.')

        with open(json_path, 'r') as file_to_read:
            settings = json.load(file_to_read)

        # Check if all settings are avaliable and valid

        self.set_maya_file(settings['maya_file'])
        self.set_project(settings['project_path'])
        self.set_start_frame(settings['start_frame'])
        self.set_end_frame(settings['end_frame'])

        self.maya_file_modification_time = settings['maya_file_modification_time']
        self.maya_version = settings['maya_version']
        self.render_engine = settings['render_engine']
        self.render_layers = settings['render_layers']

        return True

    def is_maya_file_valid(self, maya_file: str) -> bool:
        """Checks if the maya file exists."""
        if not maya_file:
            self.logger.error('Maya file has not been set.')
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

    async def get_render_progress(self, log_line: str) -> int:
        """Gets the render progress."""
        if self.render_engine == MayaRender.ARNOLD:
            pattern = r'(\d+)% done'
            match = re.search(pattern, log_line)

            if match:
                percentage = match.group(1)
                return int(percentage)
            else:
                return -1

    async def print_render_progress(self):
        """Prints the render progress."""
        while True:
            log_line = await self.render_subprocess.stdout.readline()
            if log_line:
                log_line = log_line.decode().strip()

                if self.render_engine == MayaRender.ARNOLD:
                    if MayaRender.RENDER_PROGRESS_PATTERNS[MayaRender.ARNOLD] in log_line:
                        progress = await self.get_render_progress(log_line)

                        if progress < self.progress:
                            if self.render_layers:
                                if self.current_layer + 1 > len(self.render_layers):
                                    self.current_frame += 1
                                    self.current_layer = 1
                                else:
                                    self.current_layer += 1
                            else:
                                self.current_frame += 1

                        self.progress = progress

                        self.logger.info(f'Frame: {self.current_frame} '
                                         f'Layer: {self.current_layer} '
                                         f'Progress: {self.progress}%')
                else:
                    self.logger.info(log_line)
            else:
                break

    async def monitor_process(self):
        """Monitors the render process."""
        while True:
            await self.print_render_progress()
            await asyncio.sleep(5)
            if self.render_subprocess.returncode is not None:
                break

    async def render(self, json_path: str = None) -> None:
        """Renders the Maya file."""
        if json_path:
            if not self.get_settings_from_json(json_path=json_path):
                return

        if not self.is_maya_file_valid(self.maya_file):
            return
        elif not self.is_project_path_valid(self.project_path):
            return
        elif not self.render_engine:
            self.logger.error('Render engine has not been set.')
            return
        elif self.maya_file_modification_time != os.path.getmtime(self.maya_file):
            self.logger.error('Maya file has been modified.')
            return

        self.logger.info('Starting render.')

        if self.start_frame < 0 or self.end_frame < 0:
            command = [
                MayaRender.MAYA_RENDER_EXE_PATH,
                '-proj', self.project_path,
                self.maya_file]
        else:
            command = [
                MayaRender.MAYA_RENDER_EXE_PATH,
                '-s', str(self.start_frame),
                '-e', str(self.end_frame),
                '-proj', self.project_path,
                self.maya_file]

        self.current_frame = self.start_frame

        self.render_subprocess = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

        await self.monitor_process()

        exit_code = await self.render_subprocess.wait()

        if exit_code == 0:
            self.logger.info('Render completed.')

    def set_maya_file(self, maya_file: str) -> None:
        """Sets the maya file."""
        if not self.is_maya_file_valid(maya_file=maya_file):
            return

        self.maya_file = maya_file

    def set_project(self, project_path: str) -> None:
        """Sets the Maya project."""
        if not self.is_project_path_valid(project_path=project_path):
            return

        self.project_path = project_path

    def set_end_frame(self, end_frame: int) -> None:
        """Sets the end frame."""
        if not isinstance(end_frame, (int, float)):
            self.logger.error('End frame must be an int value.')
            return

        self.end_frame = int(end_frame)

        if self.end_frame < self.start_frame:
            self.start_frame = self.end_frame

            self.logger.info(f'Start frame was set to {self.start_frame}')

    def set_start_frame(self, start_frame: int) -> None:
        """Sets the start frame."""
        if not isinstance(start_frame, (int, float)):
            self.logger.error('Start frame must be an int value.')
            return

        self.start_frame = int(start_frame)

        if self.start_frame > self.end_frame:
            self.end_frame = self.start_frame

            self.logger.info(f'End frame was set to {self.end_frame}')

    def stop_render(self) -> None:
        """Stops the render."""
        pass
        """if task.done():
            self.logger.debug(f'cleaning up finished task: {task.get_name()}')
            continue
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            self.logger.debug(f'Cancelled Task {task.get_name()}')"""


def main():
    """"""
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    custom_logger = logging.getLogger(__name__)
    custom_logger.addHandler(handler)
    custom_logger.setLevel(logging.DEBUG)

    loop = asyncio.new_event_loop()
    maya_render = MayaRender(event_loop=loop, logger=custom_logger)
    loop.create_task(maya_render.render('Z:/eMaya_project/data/test.json'))
    loop.run_forever()


if __name__ == '__main__':
    main()
