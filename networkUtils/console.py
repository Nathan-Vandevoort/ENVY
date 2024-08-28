import websockets, asyncio, socket, logging, json
import config_bridge as config
from networkUtils.message_purpose import Message_Purpose
from queue import Queue
from envyLib import envy_utils as eutils
from networkUtils import message as m
from envyLib.envy_utils import DummyLogger

class Console:

    def __init__(self, event_loop, send_queue: Queue, receive_queue: Queue, logger: logging.Logger = None):
        self.logger = logger or DummyLogger()

        self.logger.debug('networkUtils.Console: initializing')

        configs = config.Config()
        self.port = configs.DISCOVERYPORT
        self.server_file_path = configs.ENVYPATH + 'Connections/server.txt'

        self.hostname = socket.gethostname()
        self.my_ip = socket.gethostbyname(self.hostname)

        self.hash = eutils.get_hash()

        self.running = False

        self.event_loop = event_loop

        self.send_queue = send_queue
        self.receive_queue = receive_queue

        self.websocket = None

    # handles incoming messages
    async def consumer_handler(self):
        client_ip = self.websocket.remote_address[0]
        self.logger.debug(f"handling connection from: {client_ip}")
        try:
            async for message in self.websocket:
                deserialized_message = json.loads(message)
                message_object = m.build_from_message_dict(deserialized_message)
                self.logger.debug(f"received message from: {client_ip}\nmessage: ({message_object})")
                await self.consumer(message_object)
        except (websockets.exceptions.ConnectionClosedError, websockets.ConnectionClosed, websockets.ConnectionClosedOK):
            self.logger.debug(f'connection closed with server')
            return 0

    # do from incoming connection
    async def consumer(self, message):
        self.logger.debug(f'received message -> ({message})')
        self.receive_queue.put(message)
        return True

    # handles sending messages to server
    async def producer_handler(self):
        while self.running:
            while self.send_queue.empty():  # wait for something to send
                await asyncio.sleep(.1)

            message = self.send_queue.get()
            self.logger.debug(f'sending message to server: ({message})')
            status = await self.producer(message)
            if status == False:
                self.logger.debug('failed producer')
                continue
            message = message.encode()
            await self.websocket.send(message)

    async def producer(self, message):
        if not isinstance(message, m.Message) and not issubclass(message, m.Message):
            self.logger.debug('purging not message object from queue')
            return False
        return True

    async def connect(self, purpose=Message_Purpose.CONSOLE, timeout=5) -> websockets.WebSocketClientProtocol | None:
        server_ip = eutils.get_server_ip(logger=self.logger)
        uri = f"ws://{server_ip}:{self.port}/{purpose}"
        self.logger.debug(f"attempting to connect with server at {uri}")

        headers = {
            'Passkey': self.hash,
            'Name': self.hostname
        }

        try:
            websocket = await websockets.connect(uri, extra_headers=headers, timeout=timeout)
            if websocket.open:
                self.websocket = websocket
                self.logger.info('Connected to server')
                return websocket
        except (
            websockets.exceptions.ConnectionClosedError,
            asyncio.TimeoutError,
            ConnectionError
                ):
            return None
        return None

    async def start(self):
        self.logger.debug(f'networkUtils.console started')

        self.running = True
        consumer_task = self.event_loop.create_task(self.consumer_handler())
        producer_task = self.event_loop.create_task(self.producer_handler())

        console_tasks = [consumer_task, producer_task]

        while self.websocket.open:
            await asyncio.sleep(.1)

        for task in console_tasks:
            task.cancel()

        self.running = False
        self.websocket = None
        self.logger.warning('connection closed with server')
        return


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    con = Console()
