import asyncio
import websockets.exceptions
from networkUtils import client
from networkUtils.message_purpose import Message_Purpose
import logging, socket, os, sys
from queue import Queue
from envyLib import envy_utils as eutils
import time
from envyLib.envy_utils import DummyLogger
from networkUtils import message as m
from envyJobs.enums import Status
import subprocess
import config_bridge as config
import safe_exit
import psutil

NV = sys.modules.get('Envy_Functions')  # get user defined Envy_Functions as NV
ENVYPATH = os.environ['ENVYPATH']
ENVY_FUNCTIONS = eutils.list_functions_in_file(os.path.join(ENVYPATH, 'Plugins', 'Envy_Functions' + '.py'))



class Envy:

    def __init__(self, event_loop, logger: logging.Logger = None):
        self.logger = logger or DummyLogger()

        configs = config.Config()
        self.port = configs.DISCOVERYPORT
        self.server_directory = ENVYPATH + 'Connections/'

        self.hostname = socket.gethostname()
        self.my_ip = socket.gethostbyname(self.hostname)

        self.hash = eutils.get_hash()

        self.client_receive_queue = Queue(maxsize=0)
        self.client_send_queue = Queue(maxsize=0)
        self.server_receive_queue = Queue(maxsize=0)

        self.event_loop = event_loop
        self.running = None
        self.restart_on_exit = False

        # ------------------ Server / Client -------------------------
        self.role = None
        self.server = None
        self.client = None
        self.server_task = None
        self.client_task = None
        self.server_name = None

        self.client_dependant_tasks = []

        # ------------------ job attributes -------------------------
        self.job = None
        self.status = Status.IDLE

        safe_exit.register(self.exit_function)

    async def choose_role(self, role_override: Message_Purpose = None) -> Message_Purpose:
        self.logger.debug('choosing role')

        if role_override:  # if role override detected
            self.logger.debug(f'role_override detected, setting self to {role_override}')
            return role_override

        server_ip = eutils.get_server_ip()
        success = await self.client.health_check_server()
        self.logger.debug(f'server health check status: {success}')

        if success:  # if you were able to health check the server you are a client now
            self.logger.debug('I am a Client')
            return Message_Purpose.CLIENT

        #  check to see if the ip changed
        if server_ip == eutils.get_server_ip():
            # that means that you are now the server
            self.logger.debug('I am the server')
            return Message_Purpose.SERVER

        return await self.choose_role()

    async def execute(self, message: m.FunctionMessage) -> bool:
        function = message.as_function()
        try:
            self.event_loop.create_task(self.async_exec('await NV.' + function))
        except Exception as e:
            self.logger.error(f'Failed while executing {function}, {e}')
            error_message = m.Message('server_error_message')
            error_message.set_purpose(Message_Purpose.MEDIUM_SERVER_ERROR)
            error_message.set_message(f'Failed while executing {function}, {e}')
            return False
        return True

    async def execution_loop(self):
        while self.running:
            # stop blocking thread so other coroutines can run
            await asyncio.sleep(.1)
            # if you have something in your queue do it
            if not self.client_receive_queue.empty():
                job = self.client_receive_queue.get()
                await self.execute(job)

    def send(self, message: m.Message | m.FunctionMessage) -> None:
        self.client_send_queue.put(message)

    def check_server_file(self):
        self.logger.debug('writing server file')
        try:
            os.rename(f'{self.server_directory}server.txt',
                      f'{self.server_directory}server.txt')  # rename file to same name to check if its being used by another server
            return True
        except OSError:
            return False

    async def start_server(self):
        plugin_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server.py')
        cmd = ['python', plugin_path]
        flags = subprocess.CREATE_NO_WINDOW | subprocess.HIGH_PRIORITY_CLASS
        if self.check_server_file():
            self.server = subprocess.Popen(cmd, creationflags=flags, env=os.environ.copy())
            await asyncio.sleep(1)

    async def start(self, role_override=None):
        self.running = True
        self.client = client.Client(send_queue=self.client_send_queue, receive_queue=self.client_receive_queue, event_loop=self.event_loop,
                                    logger=self.logger)
        self.role = await self.choose_role(role_override)
        execution_loop_task = self.event_loop.create_task(self.execution_loop())
        execution_loop_task.set_name('envyCore.envy.execution_loop')
        self.logger.info('Started Envy')
        while self.running:
            result = await self.connect()

            if result == 0:
                sys.exit(0)

            if result == 1:  # elect new server
                self.elect_server()

    async def connect(self) -> None | int:
        """
        connects server and client depending on what the role attribute is set to
        returns various integers with different meanings
        0: something fucked up and you cant try again
        1: elect a new server

        :return: int
        """
        await NV.send_status_to_server(self)  # add a message to the send queue

        self.logger.debug(f'envy.connect: Purpose is {self.role}')
        if self.role == Message_Purpose.SERVER:
            self.server_task = await self.start_server()

        # Client connection
        success, exception, info = await self.client.connect()
        if not success:  # if client failed to connect
            self.logger.info('Failed to connect to server')

            if isinstance(exception,
                          asyncio.TimeoutError):  # if you failed to connect because the connection timed out you probably are the new server
                self.logger.info('Failed to connect because of timeout')
                self.logger.debug(f'Info: {info}, exception type: {type(exception)}')
                return 1  # elect new server

            if isinstance(exception,
                          websockets.exceptions.ConnectionClosed):  # the connection was closed for a websocket reason
                self.logger.info('Failed to connect because of websockets.ConnectionClosed')
                self.logger.debug(f'Info: {info}, exception type: {type(exception)}')
                return 1  # elect new server

            if isinstance(exception,
                          websockets.exceptions.InvalidStatusCode):  # if the connection was refused for some reason
                self.logger.info('Failed to connect because of invalid status code')
                self.logger.debug(f'Info: {info}, exception type: {type(exception)}')
                status_code = exception.status_code

                if status_code == 403:  # invalid passkey
                    self.logger.debug(
                        "server exists but I supplied the wrong hash, That's probably someone else's server")
                    return 1  # elect new server

                if status_code == 500:  # duplicate connection from host
                    self.logger.debug('Another connection from this host to that server already exists')
                    self.logger.warning(f'Envy already has another connection from {self.hostname}')
                    input('Press Enter to close')
                    return 0

            if isinstance(exception, Exception):  # the connection failed for a general reason
                self.logger.info('Failed to connect for a general reason')
                self.logger.debug(f'Info: {info}, exception type: {type(exception)}')
                return 1

            self.logger.info(f'connection failed')
            return 0

        else:  # client was able to connect
            await self.client.start()  # program will hold here until client disconnects

            self.logger.debug('cleaning up envy.client_dependant_tasks')
            for i, task in enumerate(self.client_dependant_tasks):  # cancel tasks
                self.logger.debug(f'cancelling task {task.get_name()}')
                self.client_dependant_tasks.pop(i)
                if task.done():
                    self.logger.debug(f'cleaning up finished task: {task.get_name()}')
                    continue
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    self.logger.debug(f'Cancelled Task {task.get_name()}')

        return 1  # elect new server

    def elect_server(self):
        self.logger.info('electing new server')
        clients = eutils.get_clients_from_file(logger=self.logger)

        if self.server_name == self.hostname:
            self.role = Message_Purpose.SERVER
            return

        if self.server_name in clients:
            self.logger.debug('removing old server from eligible clients')
            del clients[self.server_name]

        clients = [*clients]
        clients.sort()
        new_server = clients[0]
        self.logger.debug(f'New server: {new_server}')
        if self.hostname == new_server:  # I am the new server
            self.role = Message_Purpose.SERVER
            return

        else:
            time.sleep(5)

    async def stop(self) -> None:
        self.running = False

    async def set_status_idle(self) -> None:
        self.status = Status.IDLE
        await NV.send_status_to_server(self)  # add a message to the send queue

    async def set_status_working(self) -> None:
        self.status = Status.WORKING
        await NV.send_status_to_server(self)  # add a message to the send queue

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
        coroutine = eval(code)
        if coroutine is not None:
            await coroutine

    def exit_function(self):
        self.logger.debug(f'envy: exiting')
        parent = psutil.Process()
        for child in parent.children(recursive=True):
            try:
                child.terminate()
                self.logger.debug(f'envy: Terminating process - {child.pid}')
            except psutil.NoSuchProcess:
                self.logger.debug(f'envy: Terminated process - {child.pid}')
                pass

        if self.restart_on_exit == True:
            os.startfile(f"launch_envy.py", cwd=str(ENVYPATH), show_cmd=True)
            quit()


if __name__ == '__main__':
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    loop = asyncio.new_event_loop()
    envy = Envy(loop, logger=logger)
    loop.create_task(envy.start())
    loop.run_forever()
