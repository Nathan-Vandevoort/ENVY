import prep_env
import os, asyncio, sys, logging, socket
from networkUtils.console import Console as network_console
from queue import Queue
from networkUtils.purpose import Purpose
from envyLib import envy_utils as eutils
import time
from envyLib.colors import Colors as c
import config
from networkUtils import message as m
from envyLib.envy_utils import DummyLogger

CONSOLE = sys.modules.get('Console_Functions')  # import custom IO functions
ENVYPATH = config.Config.ENVYPATH
ENVY_FUNCTIONS = eutils.list_functions_in_file(os.path.join(ENVYPATH, 'Plugins', 'Envy_Functions' + '.py'))


class Console:

    def __init__(self, event_loop, logger: logging.Logger = None):
        self.logger = logger or DummyLogger()
        self.event_loop = event_loop
        self.send_queue = Queue(maxsize=0)
        self.receive_queue = Queue(maxsize=0)
        self.hostname = socket.gethostname()

        # make network_console
        self.con = network_console(event_loop=self.event_loop, send_queue=self.send_queue,
                                   receive_queue=self.receive_queue, logger=self.logger)

        # running
        self.running = False

        self.clients_buffer = {}

    async def ainput_continuous(self):
        while self.running:
            user_input = await eutils.ainput(f'{c.CYAN}User Input: {c.WHITE}')
            self.logger.debug(f'input: {user_input}')
            user_input = user_input.rstrip()
            valid_input = False
            function = None
            classifier = None
            try:
                valid_input, function, classifier = await self.parse_input(user_input)
            except Exception:
                valid_input = False
            if not valid_input:  # assume console is supposed to run it and give it a shot
                try:
                    self.logger.debug(f'executing {user_input}')
                    exec(f'CONSOLE.{eutils.insert_self_in_function(user_input)}')
                    continue
                except Exception as e:
                    self.write(f"{c.RED}Error: {c.WHITE}{e}")
                    continue

            # check if function exists
            function_exists = eutils.check_if_function_exists(function, ENVY_FUNCTIONS)
            if not function_exists:
                self.write(f"{c.RED}Error: {c.WHITE}Function {function} cannot be found in Plugins/Envy_Functions.py")
                continue

    def add_to_send_queue(self, message: m.Message) -> None:
        self.send_queue.put(message)

    async def consumer_handler(self):
        while self.receive_queue.empty():
            await asyncio.sleep(.1)
        await self.consumer(self.receive_queue.get())

    async def consumer(self, message: m.Message | m.FunctionMessage):
        purpose = message.get_purpose()

        if purpose == Purpose.SERVER_RESPONSE:
            print(message)
            return True

        if purpose == Purpose.FUNCTION_MESSAGE:
            await self.execute(message)

        if purpose == Purpose.SMALL_SERVER_ERROR:
            self.logger.info(f'Small server error occurred: {message} -> {message.get_message()}')
            return True

        if purpose == Purpose.MEDIUM_SERVER_ERROR:
            self.logger.warning(f'Medium server error occurred: {message} -> {message.get_message()}')
            return True

        if purpose == Purpose.LARGE_SERVER_ERROR:
            self.logger.error(f'Large server error occurred: {message} -> {message.get_message()}')
            return True

        self.logger.debug(f'unknown message received {message} -> {message.get_message()}')
        return False

    async def execute(self, job: m.FunctionMessage) -> None:
        purpose = job.get_purpose()

        if purpose == Purpose.FUNCTION_MESSAGE:
            function_string = job.as_function()
            try:
                exec(f"CONSOLE.{function_string}")
            except Exception as e:
                self.logger.debug(f'Failed to execute {job} -> {e}')
                pass

    # start console
    async def start(self, timeout=5):
        self.running = True

        # connect websocket
        websocket = await self.con.connect(timeout=timeout)
        if not websocket:
            self.logger.warning('Failed to connect to server')
            result = input('Try again (y/n)').rstrip()

            while result.upper() != 'Y' and result.upper() != 'N':  # sanitize input from user
                self.logger.warning('Please input y or n')
                result = input('Try again (y/n)').rstrip()

            if result.upper() == 'Y':  # if user wants to try again
                await self.start(timeout=5)

            else:  # if user does not want to try again
                self.logger.info('Closing Console...')
                await eutils.shutdown_event_loop(self.event_loop, logger=self.logger)
                sys.exit(0)

        start_network_console_task = self.event_loop.create_task(self.con.start())  # start console
        start_network_console_task.set_name('networkUtils.console.start')
        ainput_continuous_task = self.event_loop.create_task(self.ainput_continuous())  # start accepting input
        ainput_continuous_task.set_name('envyCore.console.ainput_continuous')
        consumer_task = self.event_loop.create_task(self.consumer_handler())
        consumer_task.set_name('envyCore.console.consumer_handler')
        console_tasks = [start_network_console_task, ainput_continuous_task, consumer_task]

        CONSOLE.request_clients(self)

        # Wait for something to happen to any of the tasks
        done, pending = await asyncio.wait(
            [start_network_console_task],
            return_when=asyncio.FIRST_EXCEPTION,
        )

        # Connection with server lost for any reason
        self.logger.warning('connection with server lost')

        for task in console_tasks:  # cancel tasks
            self.logger.debug(f'cleaning up task {task.get_name()}')
            if task.done():
                continue
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                self.logger.debug(f'Cancelled Task {task.get_name()}')

        #attempt to reconnect with server
        self.logger.info('attempting to reconnect with server...')
        time.sleep(1)
        await self.start(timeout=15)

    # parses user input, First layer of validation of user input
    async def parse_input(self, user_input: str) -> tuple:
        """
        returns tuple (True, function, classifier) if input is valid to be sent to server
        returns (false, None, None) if not
        :param user_input: String to check for input validity
        :return: tuple (success, function | None, classifier | None)
        """
        self.logger.debug(f'parsing input on {user_input}')
        if user_input.split()[0].upper() in ["SELF", "ME", "CURRENT"]:  # if user is communicating with current computer
            sSplit = user_input.split()
            sSplit[0] = self.hostname
            user_input = ' '.join(sSplit)

        try:  # try to see if input contains a function
            function = eutils.extract_function(user_input)[0].rstrip().lstrip()
            self.logger.debug(f'function: {function}')
            classifier = eutils.extract_function(user_input)[1].rstrip().lstrip()
            self.logger.debug(f'classifier: {classifier}')
        except SyntaxError as syntaxErr:
            self.write(f"{c.RED}Syntax Error while validating input: {c.WHITE}{str(syntaxErr)}")
            return False, None, None

        if eutils.validate_classifier(classifier,
                                      logger=self.logger):  # if classifier does not pass the validate_classifier check
            self.logger.debug(f'classifier: {classifier} valid')
            return True, function, classifier

        self.logger.debug(f'classifier: {classifier} invalid')
        return False, None, None

    @staticmethod
    def write(s):
        print(f"{c.GREEN}EnvyIO: {c.CLEAR}{s}")


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    con = Console(event_loop=loop)
    loop.create_task(con.start())
    loop.run_forever()
