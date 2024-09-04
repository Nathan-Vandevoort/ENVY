import asyncio, sys, logging
from envyRepo.networkUtils.client import Client
from queue import Queue
from envyRepo.networkUtils.message_purpose import Message_Purpose
from envyRepo.envyLib import envy_utils as eutils
from envyRepo.envyLib.colors import Colors as c
import envy.config_bridge as config
from envyRepo.networkUtils import message as m
from envyRepo.envyLib.envy_utils import DummyLogger
import websockets
import os

NV = sys.modules.get('Envy_Functions')
SRV = sys.modules.get('Server_Functions')
CONSOLE = sys.modules.get('Console_Functions')  # import custom IO functions

class Console:
    def __init__(self, event_loop, input_queue=None, stand_alone: bool = True, logger: logging.Logger = None, console_widget=None):
        self.event_loop = event_loop
        self.logger = logger or DummyLogger()
        self.send_queue = Queue(maxsize=0)
        self.receive_queue = Queue(maxsize=0)

        # IO
        self.input_queue = input_queue

        # console state
        self.connected = False
        self.stand_alone = stand_alone
        self.console_widget = console_widget
        self.coroutines = []
        self.client_dependant_coroutines = []

        # networking
        self.client = Client(event_loop=self.event_loop, send_queue=self.send_queue, receive_queue=self.receive_queue, logger=self.logger, purpose=Message_Purpose.CONSOLE)

        # Buffers
        self.clients = {}

    def send(self, message: m.Message | m.FunctionMessage) -> None:
        self.send_queue.put(message)

    async def checkFunctionVersions(self):
        import importlib.util

        # check envy_functions.py version
        spec = importlib.util.spec_from_file_location('Envy_Functions', os.path.join(config.Config.REPOPATH, 'envy', 'Plugins', 'Envy_Functions.py'))
        source_envy_functions = importlib.util.module_from_spec(spec)
        # sys.modules['source_envy_functions'] = source_envy_functions
        spec.loader.exec_module(source_envy_functions)
        version = await NV.version(None)
        target_version = await source_envy_functions.version(None)
        if version != target_version:
            await CONSOLE.version_mismatch(self, 'Envy_Functions', os.path.join(config.Config.REPOPATH, 'envy', 'Plugins', 'Envy_Functions.py'), os.path.join(config.Config.ENVYPATH, 'Plugins', 'Envy_Functions.py'))
            await CONSOLE.restart_envy(self, force=True)

        # check server_functions.py version
        spec = importlib.util.spec_from_file_location('Server_Functions', os.path.join(config.Config.REPOPATH, 'envy', 'Plugins', 'Server_Functions.py'))
        source_server_functions = importlib.util.module_from_spec(spec)
        # sys.modules['source_envy_functions'] = source_envy_functions
        spec.loader.exec_module(source_server_functions)
        version = await SRV.version(None)
        target_version = await source_server_functions.version(None)
        if version != target_version:
            await CONSOLE.version_mismatch(self, 'Server_Functions', os.path.join(config.Config.REPOPATH, 'envy', 'Plugins', 'Server_Functions.py'), os.path.join(config.Config.ENVYPATH, 'Plugins', 'Server_Functions.py'))
            await CONSOLE.restart_envy(self, force=True)

        # check console_functions.py version
        spec = importlib.util.spec_from_file_location('Console_Functions', os.path.join(config.Config.REPOPATH, 'envy', 'Plugins', 'Console_Functions.py'))
        source_console_functions = importlib.util.module_from_spec(spec)
        # sys.modules['source_envy_functions'] = source_envy_functions
        spec.loader.exec_module(source_console_functions)
        version = await CONSOLE.version(None)
        target_version = await source_console_functions.version(None)
        if version != target_version:
            await CONSOLE.version_mismatch(self, 'Console_Functions', os.path.join(config.Config.REPOPATH, 'envy', 'Plugins', 'Console_Functions.py'), os.path.join(config.Config.ENVYPATH, 'Plugins', 'Console_Functions.py'))
            await CONSOLE.restart_envy(self, force=True)
            self.display_warning('Console Functions were updated please reopen console')
            quit()

    async def user_input(self):
        while True:
            user_input = await eutils.ainput(f'{c.CYAN}User Input: {c.CLEAR}')
            user_input = user_input.rstrip()
            if self.connected is False:
                self.display_warning('Console is not connected to Envy network. Your message may not be received')
            try:
                self.logger.debug(f'executing {user_input}')
                await self.execute(eutils.insert_self_in_function(user_input))
            except Exception as e:
                self.display_error(e)

    async def user_input_from_queue(self):
        while True:
            if self.input_queue.empty():
                await asyncio.sleep(.1)
                continue
            user_input = self.input_queue.get()
            user_input = user_input.rstrip()
            if self.connected is False:
                self.display_warning('Console is not connected to Envy network. Your message may not be received')
            try:
                self.logger.debug(f'executing {user_input}')
                await self.execute(eutils.insert_self_in_function(user_input))
            except Exception as e:
                self.display_error(e)

    async def next_input(self, input_string: str) -> str:
        if self.stand_alone is True:
            return input(input_string)
        else:
            while self.input_queue.empty():
                await asyncio.sleep(.01)
            return self.input_queue.get().rstrip()

    async def consumer_handler(self):
        while True:
            if self.receive_queue.empty():
                await asyncio.sleep(.1)
                continue
            await self.consumer(self.receive_queue.get())

    async def consumer(self, message: m.Message | m.FunctionMessage):
        purpose = message.get_purpose()

        if purpose == Message_Purpose.FUNCTION_MESSAGE:
            function_string = message.as_function()
            self.event_loop.create_task(self.execute(function_string))
            return

        self.display_warning(f'Unknown message received {message}')
        self.display_info(f'{message}: {message.as_dict()}')

    async def execute(self, function_string: str) -> any:
        self.display_info(f'Executing: {function_string}')
        try:
            await self.async_exec(f'await CONSOLE.{function_string}')
        except Exception as e:
            self.display_error(f'Failed to execute {function_string} -> {e}')

    async def start(self):
        await self.checkFunctionVersions()

        if self.stand_alone is True:
            user_input_task = self.event_loop.create_task(self.user_input())
            user_input_task.set_name('User_Input_Task')
            self.coroutines.append(user_input_task)

        else:
            user_input_task = self.event_loop.create_task(self.user_input_from_queue())
            user_input_task.set_name('User_Input_Task')
            self.coroutines.append(user_input_task)

        consumer_task = self.event_loop.create_task(self.consumer_handler())
        consumer_task.set_name('Consumer_Task')
        self.coroutines.append(consumer_task)

        while True:
            result = await self.connect()
            await asyncio.sleep(5)

    async def async_exec(self, s: str) -> None:
        """
        this one is a copy of the one in envy_utils but I put it here so it has access to the prepared environment
        an Async version of exec that I found on stack overflow and tbh idk how it works
        -Nathan

        :param s: input string
        :return: None
        """
        import ast
        self.logger.debug(f'executing: {s}')
        code = compile(
            s,
            '<string>',
            'exec',
            flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
        )
        try:
            coroutine = eval(code)
            if coroutine is not None:
                await coroutine
        except Exception as e:
            self.display_error(e)

    async def connect(self) -> None | int:
        """
        connects server and client depending on what the role attribute is set to
        returns various integers with different meanings
        0: something fucked up and you cant try again

        :return: int
        """

        # Client connection
        success, exception, info = await self.client.connect(purpose=Message_Purpose.CONSOLE)
        if not success:  # if client failed to connect
            self.connected = False
            self.logger.info('Failed to connect to server')

            if isinstance(exception,
                          asyncio.TimeoutError):  # if you failed to connect because the connection timed out you probably are the new server
                self.logger.info('Failed to connect because of timeout')
                self.logger.debug(f'Info: {info}, exception type: {type(exception)}')
                return 0

            if isinstance(exception,
                          websockets.exceptions.ConnectionClosed):  # the connection was closed for a websocket reason
                self.logger.info('Failed to connect because of websockets.ConnectionClosed')
                self.logger.debug(f'Info: {info}, exception type: {type(exception)}')
                return 0

            if isinstance(exception,
                          websockets.exceptions.InvalidStatusCode):  # if the connection was refused for some reason
                self.logger.info('Failed to connect because of invalid status code')
                self.logger.debug(f'Info: {info}, exception type: {type(exception)}')
                status_code = exception.status_code

                if status_code == 403:  # invalid passkey
                    self.logger.debug(
                        "server exists but I supplied the wrong hash, That's probably someone else's server")
                    return 0

                if status_code == 500:  # duplicate connection from host
                    self.logger.debug('Another connection from this host to that server already exists')
                    self.logger.warning(f'Envy already has another connection from {self.hostname}')
                    input('Press Enter to close')
                    return 0

            if isinstance(exception, Exception):  # the connection failed for a general reason
                self.logger.info('Failed to connect for a general reason')
                self.logger.debug(f'Info: {info}, exception type: {type(exception)}')
                return 0

            self.logger.info(f'connection failed')
            return 0

        else:  # client was able to connect
            self.connected = True
            await self.client.start()  # program will hold here until client disconnects

            self.logger.debug('cleaning up envy.client_dependant_tasks')
            for i, task in enumerate(self.client_dependant_coroutines):  # cancel tasks
                self.logger.debug(f'cancelling task {task.get_name()}')
                self.coroutines.pop(i)
                if task.done():
                    self.logger.debug(f'cleaning up finished task: {task.get_name()}')
                    continue
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    self.logger.debug(f'Cancelled Task {task.get_name()}')

        return 0  # elect new server

    def display_error(self, message) -> None:
        if self.stand_alone is True:
            self.logger.error(f'{c.RED}Error: {message}{c.CLEAR}')
        else:
            self.logger.error(f'Error: {message}')

    def display_info(self, message) -> None:
        if self.stand_alone is True:
            self.logger.info(f'{c.WHITE}EnvyIO: {message}{c.CLEAR}')
        else:
            self.logger.info(f'Info: {message}')

    def display_warning(self, message) -> None:
        if self.stand_alone is True:
            self.logger.warning(f'{c.YELLOW}Warning: {message}{c.CLEAR}')
        else:
            self.logger.warning(f'Warning: {message}')