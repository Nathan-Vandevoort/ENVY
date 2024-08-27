import asyncio, sys, logging
from networkUtils.console import Console as network_console
from queue import Queue
from networkUtils.message_purpose import Message_Purpose
from envyLib import envy_utils as eutils
from envyLib.colors import Colors as c
import config_bridge as config
from networkUtils import message as m
from envyLib.envy_utils import DummyLogger
from envyJobs import jobTree
from envyDB import db

CONSOLE = sys.modules.get('Console_Functions')  # import custom IO functions

class Console:
    def __init__(self, event_loop, logger: logging.Logger = None):
        self.event_loop = event_loop
        self.logger = logger or DummyLogger()
        self.send_queue = Queue(maxsize=0)
        self.receive_queue = Queue(maxsize=0)

        # console state
        self.connected = False
        self.coroutines = []

        # networking
        self.network_console = network_console(event_loop=self.event_loop, send_queue=self.send_queue, receive_queue=self.receive_queue, logger=self.logger)

        # Buffers
        self.clients = {}

        # job system
        self.db = db.DB(logger=self.logger)
        self.jobs_tree = self.configure_job_tree()

    def configure_job_tree(self):
        self.db.start()
        jobs_tree = jobTree.JobTree(logger=self.logger)
        jobs_tree.enable_read_only()
        jobs_tree.skip_complete_allocations = False
        jobs_tree.skip_complete_tasks = False
        jobs_tree.set_db(self.db)
        jobs_tree.build_from_db()
        return jobs_tree

    def send(self, message: m.Message | m.FunctionMessage) -> None:
        self.send_queue.put(message)

    async def user_input(self):
        while True:
            user_input = await eutils.ainput(f'{c.CYAN}User Input: {c.CLEAR}')
            user_input = user_input.rstrip()
            if self.connected is False:
                self.display_warning('Console is not connected to Envy network. Your message may not be received')
            try:
                self.logger.debug(f'executing {user_input}')
                exec(f'CONSOLE.{eutils.insert_self_in_function(user_input)}')
            except Exception as e:
                self.display_error(e)

    async def consumer_handler(self):
        while True:
            if self.receive_queue.empty():
                await asyncio.sleep(.1)
                continue
            await self.consumer(self.receive_queue.get())

    async def consumer(self, message: m.Message | m.FunctionMessage):
        purpose = message.get_purpose()

        if purpose == Message_Purpose.FUNCTION_MESSAGE:
            await self.execute(message)
            return

        self.display_warning(f'Unknown message received {message}')
        self.display_info(f'{message}: {message.as_dict()}')

    async def execute(self, message: m.FunctionMessage) -> any:
        self.display_info(f'Executing: {message}')
        function_string = message.as_function()
        try:
            exec(f'CONSOLE.{function_string}')
        except Exception as e:
            self.display_error(f'Failed to execute {message} -> {e}')

    async def start(self):
        user_input_task = self.event_loop.create_task(self.user_input())
        user_input_task.set_name('User_Input_Task')
        self.coroutines.append(user_input_task)

        consumer_task = self.event_loop.create_task(self.consumer_handler())
        consumer_task.set_name('Consumer_Task')
        self.coroutines.append(consumer_task)

        while True:
            websocket = await self.network_console.connect()
            if websocket is None:
                self.connected = False
                self.display_info('Failed to connect to server')
                continue

            self.connected = True
            await self.network_console.start()

            self.display_warning('Connection with server lost')
            self.connected = False

    @staticmethod
    def display_error(message) -> None:
        print(f'{c.RED}Error: {message}{c.CLEAR}')

    @staticmethod
    def display_info(message) -> None:
        print(f'{c.WHITE}EnvyIO: {message}{c.CLEAR}')

    @staticmethod
    def display_warning(message) -> None:
        print(f'{c.YELLOW} Warning: {message}{c.CLEAR}')