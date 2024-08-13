import asyncio
import logging
import os
from config import Config
import json
import re
from networkUtils.purpose import Purpose


class DummyLogger:
    """
    Creates A DummyLogger object which is just an object that does nothing
    """

    def __getattr__(self, name):
        """
        when any attribute on DummyLogger is accessed the dummy() function is called which does nothing

        :param name: The name of the attribute being accessed
        :return: dummy function
        """

        def dummy(*args, **kwargs):
            pass

        return dummy


def list_functions_in_file(filename: str) -> list:
    """
    Accepts a filepath and gathers all the function names within that python file.

    :param filename: (str) path to a python file
    :return: list of function names in a python file
    """
    import ast
    with open(filename, "r") as file:
        tree = ast.parse(file.read(), filename=filename)

    functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    return functions


def write_and_flush(string: str) -> None:
    """
    writes a string to the stdout and then flushes the send buffer

    :param string: the string to write to the stdout
    :return: Void
    """
    import sys
    sys.stdout.write(f'{string}')
    sys.stdout.flush()
    return None


async def ainput(input_string: str) -> str:
    """
    Acts as an async version if the input() function

    :param input_string: text that is sent to the user
    :return: string which contains user input
    """
    import asyncio, sys
    await asyncio.to_thread(write_and_flush, f'{input_string} ')
    return await asyncio.to_thread(sys.stdin.readline)


async def shutdown_event_loop(event_loop: asyncio.AbstractEventLoop, logger: logging.Logger = None) -> None:
    """
    cancels all currently running tasks and stops the event loop

    :param event_loop: An asyncio AbstractEventLoop object
    :param logger: Optional Logger object to have this function log what it does to debug
    :return: Void
    """
    logger = logger or DummyLogger()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        logger.debug(f'cancelling task {task}')
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    event_loop.stop()
    logger.debug('event loop stopped')


def get_server_ip(logger: logging.Logger = None) -> str:  # returns the ip address of the server and null if failed
    """
    Returns IP address present in the server file. If there is no server file it will return the callers IP

    :param logger: Optional logger object to print to debug
    :return: string IP address
    """
    logger = logger or DummyLogger()
    logger.debug('getting server IP')
    server_file_path = Config.ENVYPATH + 'Connections/server.txt'

    # check if server file exists. If it does not create exist you are the server
    if not os.path.isfile(server_file_path):
        import socket
        hostname = socket.gethostname()
        my_ip = socket.gethostbyname(hostname)
        logger.debug(f'server file not found in: {server_file_path}')
        return my_ip

    else:
        logger.debug('server file found')
        server_ip = None
        with open(server_file_path, 'r') as server_file:
            server_ip = server_file.read()
        logger.debug(f'server ip address is: {server_ip}')
        return server_ip


def extract_function(s: str) -> tuple:
    """
    extracts the classifier and function out of an input string

    :param s: the input string to extract the function and classifier out of
    :return: function (str), classifier (str)
    """

    s = s.rstrip()
    if '(' not in s or ')' not in s or s[len(s) - 1] != ')':
        raise SyntaxError(f"Syntax Error: {s}")
    openIndex = s.find('(')

    counter = 0
    while True:
        counter += 1
        if s[openIndex - counter] == ' ':
            break

    startIndex = openIndex - counter
    return s[startIndex + 1:len(s)].rstrip().lstrip(), s[:startIndex]


def get_clients_from_file(logger: logging.Logger = None) -> dict:
    """
    Gets the clients dict from the clients.json file

    :param logger: Optional logger
    :return: clients dictionary from disk
    """
    logger = logger or DummyLogger()
    clients_file_path = os.path.join(Config.ENVYPATH, 'Connections/clients.json')

    clients = None
    logger.debug(f'opening clients file at {clients_file_path}')
    with open(clients_file_path, 'r') as clients_file:
        clients = json.load(clients_file)
        clients_file.close()

    logger.debug(f'returning clients: {clients}')
    return clients


def validate_classifier(classifier: str, logger: logging.Logger = None) -> bool:
    """
    validates if a classifier is valid or not
    :param classifier: (str) classifier
    :param logger: optional logger
    :return: (bool) True if classifier is valid and False if not
    """
    logger = logger or DummyLogger()
    logger.debug(f'validating classifier {classifier}')
    if classifier == '*':
        return True

    if re.search(
            '^lab[0-9*-]+\s?[0-9*-]*$|^vr\s?[0-9*-]+$|^lab[0-9]{1,2}[0-9a-z-]+[0-9]{2}$|^vr[0-9]{1,2}[0-9a-z-]+['
            '0-9]{2}$',
            classifier,
            re.IGNORECASE) is not None:  # check if classifier starts with lab or vr followed by acceptable characters and ending with a number or *
        return True
    return False


def check_if_function_exists(function: str, file_functions: list, logger: logging.Logger = None) -> bool:
    """
    returns true if function can be found within a list of functions.
    will determine name of function even if function has parenthesis

    :param function: string function to look for
    :param file_functions: list of functions to compare against
    :param logger: optional logger
    :return:
    """
    logger = logger or DummyLogger()

    parenthesis_found = False
    counter = 0
    function_length = len(function)
    char_buff = []
    while not parenthesis_found:
        char = function[counter]

        if char == '(':
            break

        if counter >= function_length:
            logger.warning('check_if_function_exists: Ran outside bounds of string while looking for "("')
            return False

        char_buff.append(char)
        counter += 1

    function_name = ''.join(char_buff)

    if function_name in file_functions:
        logger.debug('check_if_function_exists: function found')
        return True

    logger.debug('check_if_function_exists: function not found')
    return False


def digit_split(s: str) -> tuple:
    """
    Splits the numbers off the end of a string

    :param s: input string
    :return: tuple (word, numbers)
    """
    head = s.rstrip('0123456789-*')
    tail = s[len(head):]
    return head, tail


def validate_computer_against_classifier(classifier: str, hostname: str, logger: logging.Logger = None) -> bool:
    """
    Given a classifier and the name of a computer returns True/False depending on if the classifier pertains to the
    computer name

    :param classifier: str classifier
    :param hostname: str hostname or name of computer
    :param logger: optional logger
    :return: True if classifier pertains to hostname and False if not
    """
    logger = logger or DummyLogger()
    logger.debug(f'validating {hostname} against {classifier}')
    s = classifier.replace('*', '+')
    tokens = s.split()

    lab = ""
    computer = ""
    for token in tokens:

        if re.search('^(lab)|^(vr)', token, re.IGNORECASE):  #gets lab and lab number
            letters, numbers = digit_split(token)
            if len(numbers) == 0:
                lab = f"^{letters}"
            elif len(numbers) == 1:
                lab = f"{letters}{numbers}"
            elif numbers == '*':
                lab = f"^{letters}{numbers}"
            else:
                lab = f"^{letters}[{numbers}]"

        if lab == "":  #by this point the lab number should be parsed so if it's not throw an error
            return False

        if re.search('^[0-9]{0,2}(-)[0-9]{0,2}$', token,
                     re.IGNORECASE):  #checks and processes if computer number is a range
            greaterThanTenTest = [(char, len(char) == 2) for char in token.split('-')]
            newToken = [f"0[{char}-9]$|" if flag != True else f"[a-z0-9\-]*1[0-{char[-1:]}]$" for char, flag in
                        greaterThanTenTest]
            newToken = lab.join(newToken)
            computer = newToken

        if re.search('^[0-9]{0,2}$', token, re.IGNORECASE):
            computer = f"[a-z0-9-]*{token}$"

        if re.search('^[^A-Za-z0-9]', token,
                     re.IGNORECASE):  #checks if token is a special character (meant to catch wild cards)
            computer = token

    pattern = re.compile(lab + "[a-z0-9\-]*" + computer, re.IGNORECASE)
    result = re.search(pattern, hostname)

    if not result:
        logger.debug(f'not valid')
        return False

    else:
        logger.debug(f'valid')
        return True


def get_applicable_clients(classifier: str, clients: list, logger: logging.Logger = None) -> list | bool:
    """
    given a classifier and a list of clients will return True if classifier pertains to every computer in
    list or a list of clients who it does pertain to

    :param classifier: str classifier
    :param clients: list or dict of clients
    :param logger: optional logger
    :return: True if every client is valid or a list of valid clients. Can return an empty list
    """
    logger = logger or DummyLogger()

    if classifier == '*':
        return list(clients)

    valid_clients = []
    for client in clients:
        if validate_computer_against_classifier(classifier, client):
            valid_clients.append(client)

    return valid_clients


async def async_exec(s: str) -> None:
    """
    an Async version of exec that I found on stack overflow and tbh idk how it works
    edit: it works by compiling your input string to be executed. that specific ast flag allows the code to be ran as a coroutine
    -Nathan

    :param s: input string
    :return: None
    """
    import ast
    code = compile(
        s,
        '<string>',
        'exec',
        flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
    )
    coroutine = eval(code)
    if coroutine is not None:
        await coroutine


def get_hash() -> str:
    """
    generates the authentication hash out of username
    :return: (str) hash
    """
    import hashlib
    username = os.getlogin().upper()
    h = hashlib.new('sha256')
    h.update(username.encode())
    return h.hexdigest()


def insert_self_in_function(function: str) -> str:
    """
    inserts 'self' into the string representation of a function
    doSomething() -> doSomething(self)
    doSomething(arg1, arg2) -> doSomething(self, arg1, arg2)
    :param function: (str) the function to add self to
    :return: (str) input string with self injected
    """
    compressed_function = function.replace(' ', '')

    openIndex = compressed_function.find('(')

    if compressed_function[openIndex + 1] == ')':
        openIndex = function.find('(')
        return function[:openIndex + 1] + 'self' + function[openIndex + 1:]

    else:
        openIndex = function.find('(')
        return function[:openIndex + 1] + 'self, ' + function[openIndex + 1:]