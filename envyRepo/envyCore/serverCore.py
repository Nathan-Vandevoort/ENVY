import os, sys
abs_file = os.path.abspath(__file__)
sys.path.append(os.path.join(os.path.dirname(abs_file), os.pardir, os.pardir))
import envyRepo.prep_env
import socket, logging, websockets, asyncio, json
from queue import Queue
from envyRepo.networkUtils.message_purpose import Message_Purpose
from envyRepo.envyLib import envy_utils as eutils
import envyRepo.networkUtils.message as m
from envyRepo.envyJobs import scheduler
from envyRepo.envyJobs.enums import Status
import psutil
ENVYPATH = os.environ['ENVYPATH']
sys.path.insert(0, ENVYPATH)
import envy.utils.config_bridge as config
from datetime import datetime

SRV = sys.modules.get('Server_Functions')

def update_clients_file(dir, clients: dict):
    clients_file = os.path.join(dir, 'clients.json')
    clients = {k: {k2: v2 for k2, v2 in v.items() if k2 != 'Socket'} for k, v in clients.items()}
    with open(clients_file, 'w') as cf:
        json.dump(clients, cf)


class Server:

    def __init__(self, receive_queue: Queue, event_loop, logger: logging.Logger = None):
        self.logger = logger or eutils.DummyLogger()
        self.hostname = socket.gethostname()
        self.my_ip = socket.gethostbyname(self.hostname)
        self.running = False
        self.server_file = None
        
        # Set priority to high
        process = psutil.Process(os.getpid())
        process.nice(psutil.HIGH_PRIORITY_CLASS)

        configs = config.Config()
        self.port = configs.DISCOVERYPORT
        self.server = None

        self.clients = {}
        self.consoles = {}
        self.hash = eutils.get_hash()
        self.receive_queue = receive_queue
        self.event_loop = event_loop

        self.tasks = []

        # -------------------- directories ------------------------------------
        self.server_directory = os.path.join(configs.ENVYPATH, 'Connections')

        # -------------------- Job --------------------------------------
        self.job_scheduler = scheduler.Scheduler(self, self.event_loop, logger=self.logger)

    async def check_passkey(self, path, request_headers):
        passkey = request_headers.get('Passkey')
        name = request_headers.get('Name')
        self.logger.debug(f'received connection from {name} with purpose {path}')

        if path == '/client':
            if name in self.clients:
                self.logger.debug(f'rejecting client connection,Reason: client already exists {name}')
                return 500, [("Content-Type", "text/plain")], b"connection from client already exists"

        if path == '/console':
            if name in self.consoles:
                self.logger.debug(f'rejecting console connection,Reason: console already exists {name}')
                return 500, [("Content-Type", "text/plain")], b"connection from client already exists"

        if passkey != self.hash:
            self.logger.debug("Invalid Passkey, rejecting connection")
            return 403, [("Content-Type", "text/plain")], b"Invalid passkey"

        self.logger.debug(f"validated connection from {name}")
        return None

    async def handler(self, websocket):
        client_ip = websocket.remote_address[0]
        request_headers = websocket.request_headers

        if websocket.path == '/client':
            client = request_headers['Name']
            # Register new client
            await self.register_client(client, client_ip, websocket)

            # Send the client name of server
            await SRV.send_attribute_to_client(self, client, 'hostname', 'server_name')

            # Start tasks per connection
            consumer_task = asyncio.create_task(self.client_handler(websocket, client))
            done, pending = await asyncio.wait(
                [consumer_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()

            await self.unregister_client(client)

        if websocket.path == '/console':
            console = request_headers['Name']
            await self.register_console(console, client_ip, websocket)

            # Start tasks per connection
            consumer_task = asyncio.create_task(self.console_handler(websocket, console))
            done, pending = await asyncio.wait(
                [consumer_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()

            self.unregister_console(console)

        if websocket.path == '/health_check':
            await websocket.recv()
            await websocket.send('pong')

    # handles incoming messages from console
    async def console_handler(self, websocket, console):
        console_ip = websocket.remote_address[0]
        try:
            async for message in websocket:
                deserialized_message = json.loads(message)
                message_object = m.build_from_message_dict(deserialized_message)
                self.logger.info(f"Console {console} sent message: ({message_object})")
                status = await self.console_consumer(
                    message_object)  # will return True or False if the message was acted upon
                if not status:
                    self.logger.warning(f'unknown message received ({message_object}) -> {message_object.as_dict()}')
                    continue
        except (
                websockets.exceptions.ConnectionClosedError, websockets.ConnectionClosed,
                websockets.ConnectionClosedOK
        ):
            self.logger.debug(f'connection closed with {console}')
            return 0  # connection was closed

    # handles incoming messages clients
    async def client_handler(self, websocket, client):
        client_ip = websocket.remote_address[0]
        try:
            async for message in websocket:
                deserialized_message = json.loads(message)
                messageObject = m.build_from_message_dict(deserialized_message)
                self.logger.debug(f"Client {client} sent message: ({messageObject})")
                status = await self.client_consumer(
                    messageObject)  # will return True or False if the message was acted upon
                if not status:
                    self.logger.warning(f'unknown message received ({messageObject}) -> {messageObject.as_dict()}')
                    continue
        except (
                websockets.exceptions.ConnectionClosedError, websockets.ConnectionClosed,
                websockets.ConnectionClosedOK):
            self.logger.debug(f'connection closed with {client}')
            return 0  # connection was closed

    # do from incoming connection
    async def client_consumer(self, message: m.Message | m.FunctionMessage):
        purpose = message.get_purpose()

        if purpose == Message_Purpose.FUNCTION_MESSAGE:
            if not isinstance(message, m.FunctionMessage):
                self.logger.error(f"Message ({message}) is not a FunctionMessage")
                return False

            success = await self.execute(message)
            return success

        # if request is never executed
        return False

    async def execute(self, message: m.FunctionMessage) -> bool:
        self.logger.debug(f'executing {message}')
        function = message.as_function()
        try:
            await self.async_exec('await SRV.' + function)
        except Exception as e:
            self.logger.error(f'Failed while executing: {function} -> {e}')
            error_message = m.Message('server_error_message')
            error_message.set_purpose(Message_Purpose.MEDIUM_SERVER_ERROR)
            error_message.set_message(f'Failed while executing {function}, {e}')
            await SRV.send_to_consoles(self, error_message)
            return False
        return True

    async def pass_on(self, message: m.Message):
        try:
            self.logger.debug(f'pass_on: ({message})')
            function_message = m.build_from_message_dict(message.get_data(), logger=self.logger)
            classifier = message.get_message()
            send_targets = eutils.get_applicable_clients(classifier, list(self.clients))
            await SRV.send_to_clients(self, send_targets, function_message)
            return True
        except Exception:
            return False

    async def console_consumer(self, message: m.Message | m.FunctionMessage):
        self.logger.debug(f'received message from console: {message}')
        purpose = message.get_purpose()

        if purpose == Message_Purpose.FUNCTION_MESSAGE:
            if not isinstance(message, m.FunctionMessage):
                self.logger.error(f"Message ({message}) is not a FunctionMessage")
                return False

            success = await self.execute(message)
            return success

        if purpose == Message_Purpose.PASS_ON:
            success = await self.pass_on(message)
            return success

    async def register_client(self, client, ip, websocket):
        self.logger.info(f"Registering client: {client}")
        new_client_data = {
            'IP': ip,
            'Socket': websocket,
            'Status': Status.WORKING,
            'Job': None,
            'Allocation': None,
        }
        self.clients[client] = new_client_data
        update_clients_file(self.server_directory, self.clients)

        json_safe_client_data = {
            'IP': ip,
            'Status': Status.IDLE,
            'Job': None,
            'Allocation': None,
        }

        await SRV.console_register_client(self, client, json_safe_client_data)

    async def register_console(self, console, ip, websocket):
        self.logger.debug(f'Registering console {console}')
        self.consoles[console] = {
            'IP': ip,
            'Socket': websocket
        }
        await SRV.send_clients_to_console(self)

    async def unregister_client(self, client):
        self.logger.info(f'Unregistering Client {client}')
        del self.clients[client]
        update_clients_file(self.server_directory, self.clients)
        await SRV.console_unregister_client(self, client)

    def unregister_console(self, console):
        self.logger.info(f'Unregistering Console {console}')
        del self.consoles[console]

    def write_server_file(self):
        self.logger.debug('writing server file')
        try:
            os.rename(os.path.join(self.server_directory, 'server.txt'), os.path.join(self.server_directory, 'server.txt'))  # rename file to same name to check if its being used by another server
        except OSError:
            raise PermissionError('File is being used by another server')
        self.server_file = open(os.path.join(self.server_directory, 'server.txt'), 'w')
        self.server_file.write(self.my_ip)
        self.server_file.flush()

    async def start(self):
        self.logger.debug('starting server')
        try:
            self.server = await websockets.serve(self.handler, self.my_ip, self.port, process_request=self.check_passkey)
            self.write_server_file()
            scheduler_task = self.event_loop.create_task(self.job_scheduler.start())
            scheduler_task.set_name('Scheduler.start()')
            self.tasks.append(scheduler_task)
            orphan_task = self.event_loop.create_task(self.check_orphaned())
            orphan_task.set_name('check_orphaned')
            self.tasks.append(orphan_task)
            self.running = True
            await self.server.wait_closed()
        except (OSError, PermissionError):
            sys.exit(0)
        self.running = False

    async def async_exec(self, s: str) -> None:
        """
        this one is a copy of the one in envy_utils but I put it here so it has access to the prepared environment
        an Async version of exec that I found on stack overflow and tbh idk how it works
        Update: I think I do know how it works kinda.
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

    @staticmethod
    async def check_orphaned():
        parent = psutil.Process(os.getppid())
        while True:
            if not parent.is_running():
                quit(1)
            await asyncio.sleep(.5)

if __name__ == '__main__':
    os.system('color')
    class CustomFormatter(logging.Formatter):
        # Define color codes
        grey = "\x1b[38;20m"
        yellow = "\x1b[33;20m"
        red = "\x1b[31;20m"
        bold_red = "\x1b[31;1m"
        reset = "\x1b[0m"

        # Define format
        format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'

        FORMATS = {
            logging.DEBUG: grey + format + reset,
            logging.INFO: yellow + format + reset,
            logging.WARNING: yellow + format + reset,
            logging.ERROR: red + format + reset,
            logging.CRITICAL: bold_red + format + reset
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    log_path = os.path.join(str(config.Config.ENVYPATH), 'Logs', f'SERVER_{socket.gethostname()}.log')
    if not os.path.isdir(os.path.join(str(config.Config.ENVYPATH), 'Logs')):
        os.makedirs(os.path.join(str(config.Config.ENVYPATH), 'Logs'))

    if not os.path.isfile(log_path):
        with open(log_path, 'w') as file:
            file.close()
    today = datetime.now()
    current_time = today.strftime('%H:%M:%S')

    with open(log_path, 'a') as file:
        file.write(f'\n\n{today}\n{current_time}')
        file.close()

    log_handler = logging.FileHandler(log_path, 'a')
    log_handler.setFormatter(CustomFormatter())

    logger = logging.getLogger(__name__)
    logger.addHandler(log_handler)
    logger.setLevel(logging.DEBUG)
    receive_queue = Queue(maxsize=0)
    loop = asyncio.new_event_loop()
    ldr = Server(receive_queue=receive_queue, event_loop=loop, logger=logger)
    loop.create_task(ldr.start())
    loop.run_forever()
