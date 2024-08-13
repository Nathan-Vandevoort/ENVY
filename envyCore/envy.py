import asyncio
import websockets.exceptions
from networkUtils import server, client
from networkUtils.purpose import Purpose
import logging, config, socket, hashlib, os, sys
from queue import Queue
from envyLib import envy_utils as eutils
import time
from envyLib.envy_utils import DummyLogger
from networkUtils import message as m

NV = sys.modules.get('Envy_Functions')  # get user defined Envy_Functions as NV
ENVYPATH = config.Config.ENVYPATH
TIMEOUT_INTERVAL = config.Config.TIMEOUT
ENVY_FUNCTIONS = eutils.list_functions_in_file(os.path.join(ENVYPATH, 'Plugins', 'Envy_Functions' + '.py'))


class Envy:

    def __init__(self, event_loop, logger: logging.Logger = None):
        self.logger = logger or DummyLogger()

        configs = config.Config()
        self.port = configs.DISCOVERYPORT
        self.server_file_path = ENVYPATH + 'Connections/server.txt'

        self.hostname = socket.gethostname()
        self.my_ip = socket.gethostbyname(self.hostname)

        self.hash = eutils.get_hash()

        self.client_receive_queue = Queue(maxsize=0)
        self.server_receive_queue = Queue(maxsize=0)

        self.event_loop = event_loop
        self.running = None

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
        self.progress = 0.0

    async def choose_role(self, role_override: Purpose = None) -> Purpose:
        self.logger.debug('choosing role')

        if role_override:  # if role override detected
            self.logger.debug(f'role_override detected, setting self to {role_override}')
            return role_override

        success = await self.client.health_check_server()
        self.logger.debug(f'server health check status: {success}')

        if success:  # if you were able to health check the server you are a client now
            self.logger.debug('I am a Client')
            return Purpose.CLIENT

        # you failed to health check the server
        # that means that you are now the server
        self.logger.debug('I am the server')
        return Purpose.SERVER

    async def execute(self, job: m.FunctionMessage) -> None:
        purpose = job.get_purpose()

        if purpose == Purpose.FUNCTION_MESSAGE:
            function_string = job.as_function()
            try:
                exec(f"NV.{function_string}")
            except Exception as e:
                self.logger.debug(f'Failed to execute {job} -> {e}')
                pass

    async def execution_loop(self):
        while self.running:
            # stop blocking thread so other coroutines can run
            await asyncio.sleep(.1)

            # if you have something in your queue do it
            if not self.client_receive_queue.empty():
                job = self.client_receive_queue.get()
                await self.execute(job)

    async def start_server(self):
        server_task = self.event_loop.create_task(self.server.start())
        server_task.set_name('server.start')
        start_time = time.time()
        while not self.server.running:  # wait for server to start
            self.logger.debug('waiting for server')
            await asyncio.sleep(.1)
            if time.time() - start_time > TIMEOUT_INTERVAL:  # exit condition
                self.logger.error('Timed out while attempting to start server')
                self.logger.error('exiting')
                time.sleep(3)
                return None
            self.logger.debug(time.time() - start_time)
            await asyncio.sleep(.1)
        return server_task

    async def start_client(self):
        self.client_task = self.event_loop.create_task(self.client.start())
        self.client_task.set_name('client.start')
        self.client_dependant_tasks.append(self.client_task)

        start_time = time.time()
        while not self.client.running:  # wait for client to finish starting

            if time.time() - start_time > TIMEOUT_INTERVAL:
                self.logger.error('Timed out while attempting to connect with server')
                self.logger.error('exiting')
                time.sleep(3)
                sys.exit(0)

            self.logger.debug('waiting for client')
            self.logger.debug(time.time() - start_time)
            await asyncio.sleep(.1)

    async def run(self, role_override=None):
        self.running = True
        self.client = client.Client(receive_queue=self.client_receive_queue, event_loop=self.event_loop,
                                    logger=self.logger)
        self.server = server.Server(receive_queue=self.server_receive_queue, event_loop=self.event_loop,
                                    logger=self.logger)
        self.role = await self.choose_role(role_override)
        execution_loop_task = self.event_loop.create_task(self.execution_loop())
        execution_loop_task.set_name('envyCore.envy.execution_loop')

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
        self.logger.debug(f'envy.connect: Purpose is {self.role}')
        if self.role == Purpose.SERVER:
            self.server_task = await self.start_server()
            if not self.server_task:
                self.logger.warning('server failed to start')
                return 0

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
                return 0

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
        self.logger.debug('electing new server')
        clients = eutils.get_clients_from_file(logger=self.logger)

        if self.server_name in clients:
            self.logger.debug('removing old server from eligible clients')
            del clients[self.server_name]

        clients = [*clients]
        clients.sort()
        new_server = clients[0]
        self.logger.debug(f'New server: {new_server}')
        if self.hostname == new_server:  # I am the new server
            self.role = Purpose.SERVER

        else:
            time.sleep(10)

    async def stop(self) -> None:
        self.running = False


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
    loop.create_task(envy.run())
    loop.run_forever()
