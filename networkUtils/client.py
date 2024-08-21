import socket, global_config, os, logging, websockets, asyncio, hashlib, json
import __config__ as config
from queue import Queue
from networkUtils.message_purpose import Message_Purpose
from envyLib import envy_utils as eutils
from networkUtils import exceptions as network_exceptions
import networkUtils.message as m


class Client:

    def __init__(self, receive_queue: Queue, event_loop, send_queue: Queue, logger: logging.Logger = None):
        self.logger = logger or eutils.DummyLogger()
        self.hostname = socket.gethostname()
        self.my_ip = socket.gethostbyname(self.hostname)
        self.running = False

        configs = config.Config()
        self.port = configs.DISCOVERYPORT
        self.server_file_path = configs.ENVYPATH + 'Connections/server.txt'

        self.hash = eutils.get_hash()

        self.receive_queue = receive_queue

        self.send_queue = send_queue

        self.event_loop = event_loop

        self.heart_beat_interval = 10

        self.running = False

        self.websocket = None

        self.client_tasks = []

    async def health_check_server(self) -> bool:
        self.logger.debug('health checking server')
        status, exception, data = await self.connect(purpose=Message_Purpose.HEALTH_CHECK, use_logger=False)

        if not status:
            return False

        return True

    async def connect(self, purpose=Message_Purpose.CLIENT, timeout=2.5, use_logger: bool = True) -> tuple:
        logger = eutils.DummyLogger()
        if use_logger:
            logger = self.logger
        server_ip = eutils.get_server_ip(logger=logger)
        uri = f"ws://{server_ip}:{self.port}/{purpose}"
        logger.debug(f"attempting to connect with server at {uri}")

        headers = {
            'Passkey': self.hash,
            'Name': self.hostname
        }

        try:
            if purpose == Message_Purpose.HEALTH_CHECK:
                websocket = await websockets.connect(uri, extra_headers=headers, timeout=timeout)
                await websocket.send('ping')
                result = await websocket.recv()
                if result == 'pong':
                    await self.disconnect(websocket=websocket, use_logger=False)
                    return True, None, 'Connected Successfully'

            if purpose == Message_Purpose.CLIENT:
                websocket = await websockets.connect(uri, extra_headers=headers, timeout=timeout)
                if websocket.open:
                    self.websocket = websocket
                    return True, None, 'Connected Successfully'

            return False, None, 'Connection failed (It could be the purpose?)'

        except websockets.exceptions.ConnectionClosedError as connection_closed:
            return False, connection_closed, str(connection_closed)

        except asyncio.TimeoutError as timeout:
            return False, timeout, str(timeout)

        except Exception as e:
            return False, e, str(e)

    async def disconnect(self, websocket: websockets.WebSocketClientProtocol = None, use_logger: bool = True) -> None:
        logger = eutils.DummyLogger()
        if use_logger:
            logger = self.logger
        websocket = websocket or self.websocket
        if not websocket:
            logger.info('Cannot disconnect websocket does not exist')
            raise network_exceptions.ConnectionNotFoundError('Cannot disconnect a websocket which does not exist')

        if not websocket:
            return

        logger.debug('disconnecting websocket')
        await websocket.close()
        if websocket.open:
            websocket.debug('Connection failed to close')
            raise network_exceptions.OperationFailed('Failed to close connection')

        else:
            self.websocket = None
            logger.debug('Connection Closed Successfully')
            return

    async def producer_handler(self):
        while self.running:
            await asyncio.sleep(.1)
            while self.send_queue.empty():  # wait for something to send
                await asyncio.sleep(.1)

            message = self.send_queue.get()
            self.logger.debug(f'sending message to server: ({message})')
            status = await self.producer(message)
            if status == False:
                self.logger.debug('failed producer')
                continue
            message = message.encode()
            try:
                await self.websocket.send(message)
            except (websockets.exceptions.ConnectionClosed, AttributeError):
                return

    async def producer(self, message):
        if not isinstance(message, m.Message) and not issubclass(message, m.Message):
            self.logger.info('purging not message object from queue')
            return False
        return True

    async def start(self):
        self.logger.debug(f'networkUtils.client started')

        self.running = True
        consumer_task = self.event_loop.create_task(self.consumer_handler())
        consumer_task.set_name('client.consumer_handler')

        producer_task = self.event_loop.create_task(self.producer_handler())
        producer_task.set_name('client.producer')

        self.client_tasks.append(consumer_task)
        self.client_tasks.append(producer_task)

        self.logger.info('Client: Connected')
        while self.websocket.open:  # hang here while connection is open
            await asyncio.sleep(1.5)

        self.logger.warning('connection closed with server')
        await self.stop()

        return 0

    # handles incoming messages
    async def consumer_handler(self):
        client_ip = self.websocket.remote_address[0]
        self.logger.debug(f"connected to: {client_ip}")
        try:
            async for message in self.websocket:
                deserialized_message = json.loads(message)
                message_object = m.build_from_message_dict(deserialized_message)
                self.logger.info(f"received message from: server -> ({message_object})")
                status = await self.consumer(message_object)
                if not status:
                    self.logger.warning(f'unknown message received ({message_object}) -> {message_object.as_dict()}')
                    continue
        except asyncio.CancelledError:
            self.logger.debug('consumer_handler cancelled')
            raise
        except websockets.exceptions.ConnectionClosed as e:
            self.logger.debug(f'consumer_handler: {e}')

    # do from incoming connection
    async def consumer(self, message: m.FunctionMessage):
        target = message.get_target()
        if target != Message_Purpose.CLIENT:
            self.logger.warning(f"message is not for {Message_Purpose.CLIENT}")
            return False

        self.receive_queue.put(message)
        return True

    async def send(self, message: m.Message | m.FunctionMessage):
        message = message.encode()
        await self.websocket.send(message)

    async def stop(self):
        self.logger.debug('stopping client')
        self.running = False
        try:
            await self.disconnect(self.websocket)

        except network_exceptions.OperationFailed:
            return False

        except network_exceptions.ConnectionNotFoundError:
            return False

        self.logger.debug('cleaning up tasks')

        for i, task in enumerate(self.client_tasks):
            self.logger.debug(f'cancelling task {task.get_name()}')
            self.client_tasks.pop(i)
            if task.done():
                continue
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                self.logger.debug(f'cancelled task {task.get_name()}')

        self.logger.debug('client stopped')
        return True


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    receive_queue = Queue(maxsize=0)
    loop = asyncio.new_event_loop()
    me = Client(receive_queue=receive_queue, event_loop=loop)
    loop.create_task(me.start())
    loop.run_forever()
