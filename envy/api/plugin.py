from __future__ import annotations

import asyncio.subprocess
import logging
import os
import subprocess
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field, PrivateAttr

import envy
from envy import utils
from envy.api.limits import Range

logger = logging.getLogger(__name__)

PLUGIN_RANGE_VAR = 'ENVY_PLUGIN_RANGE'
PLUGIN_ARGS_VAR = 'ENVY_PLUGIN_ARGS'


class Plugin(BaseModel, ABC):
    name: str
    args: tuple = Field(default=())
    kwargs: dict = Field(default={})
    environment: dict = Field(default={})

    _proc: subprocess.Popen | None = PrivateAttr(default=None)

    def run(self, start: float, end: float, increment: float, *args, **kwargs) -> None: ...

    def frame_finished(self, frame_number: float) -> None: ...

    def task_finished(self) -> None: ...

    def error(self, error_message: str) -> None: ...

    def stop(self) -> None: ...

    async def _run(self, frame_range: Range) -> None:
        plugin = get_plugin_from_name(self.name)
        if not plugin:
            logger.error(f'Cannot find plugin with name: {self.name}')
            return
        logger.info(f'Starting plugin: {self.name}')

        # TODO: Some sort of switch to have it replace rather then update environment
        environment = os.environ
        environment.update(self.environment)
        environment[PLUGIN_RANGE_VAR] = frame_range.model_dump_json()
        environment[PLUGIN_ARGS_VAR] = self.model_dump_json()

        plugin_runner_path = os.path.join(os.path.dirname(envy.__file__), 'plugin_runner.py')
        args = ['python', plugin_runner_path]
        if os.name == 'nt':
            proc = subprocess.Popen(
                args,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                env=environment,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            proc = subprocess.Popen(
                args,
                preexec_fn=os.setsid,
                env=environment,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        self._proc = proc
        await self._monitor_process(self._proc)

    def _stop(self) -> None:
        logger.info(f'Stopping sandbox process')
        self._proc = None

    @staticmethod
    async def _monitor_process(process: subprocess.Popen) -> None:
        if not process:
            raise ValueError('No process exists to monitor')

        if not process.stdout:
            logger.debug(f'{process.stdout=}')
            raise ValueError('Sandbox process does not have valid pipe for stdout')

        if not isinstance(process.stdout, asyncio.StreamReader):
            logger.debug(f'{type(process.stdout)=}')
            raise TypeError(f'sandbox process stdout pipe must be asyncio.StreamReader')

        async for line in process.stdout:
            logger.debug(f'{line}')


def get_plugins() -> tuple[type[Plugin], ...]:
    """
    Return all plugins gathered by searching for subclasses of
    Plugin in the plugin directory.
    """

    plugins: list[type[Plugin]] = []
    envy_dir = os.path.dirname(envy.__file__)
    plugins_dir = os.path.join(envy_dir, 'plugins')
    for item in os.listdir(plugins_dir):
        modules = utils.get_module_names(f'envy.plugins.{item}')
        for module in modules:
            plugins.extend(utils.get_classes(module, Plugin))

    return tuple(plugins)


def get_plugin_from_name(name: str) -> type[Plugin] | None:
    plugins = get_plugins()
    for plugin in plugins:
        if plugin.name == name:
            return plugin
    return None
