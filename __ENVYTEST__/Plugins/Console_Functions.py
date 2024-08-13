import user_config, sys
sys.path.append(user_config.Config.REPOPATH)
from networkUtils import message as m
from networkUtils.purpose import Purpose
from envyLib import envy_utils as eutils
from envyLib.colors import Colors as c


def fill_buffer(console, buffer_name: str, data: any) -> None:
    """
    fills a buffer on the console given the buffers name and data to fill the buffer with
    :param console: reference to the console calling the function
    :param buffer_name: (str) name of buffer
    :param data: (any) data to fill buffer with
    :return: Void
    """
    setattr(console, buffer_name, data)


def install_maya_plugin(console) -> None:
    """
    installs the Maya plugin
    :param console: reference to the console calling the function
    """
    classifier = get_classifier(console)
    valid = eutils.validate_classifier(classifier)
    if not valid:
        console.write(f"{c.RED}Invalid classifier: {c.WHITE}{classifier}")
        return
    function_message = m.FunctionMessage('install_maya_plugin()')
    function_message.set_target(Purpose.CLIENT)
    function_message.set_function('install_maya_plugin')
    send_to_clients(console, classifier, function_message)


def request_clients(console) -> None:
    """
    Sends a message to the server requesting all the servers currently connected clients
    :param console: a reference to the console making the call
    :return: Void
    """
    function_message = m.FunctionMessage('request clients')
    function_message.set_target(Purpose.SERVER)
    function_message.set_function('send_clients_to_console')
    function_message.format_arguments(target_consoles=console.hostname)
    console.add_to_send_queue(function_message)


def restart_envy(console) -> None:
    """
    restart envy instances
    :param console: reference to the console making the call
    :return: Void
    """
    classifier = get_classifier(console)
    valid = eutils.validate_classifier(classifier)
    if not valid:
        console.write(f"{c.RED}Invalid classifier: {c.WHITE}{classifier}")
        return
    function_message = m.FunctionMessage('restart_envy()')
    function_message.set_target(Purpose.CLIENT)
    function_message.set_function('restart_envy')
    send_to_clients(console, classifier, function_message)


def get_classifier(console):
    console.write("Classifier (What computers to affect)?")
    classifier = input(f"{c.CYAN}UserInput: {c.WHITE}").rstrip()
    return classifier


def debug_envy(console) -> None:
    """
    has envy run its debug function
    :param console: reference to the console calling this function
    :return: Void
    """
    classifier = get_classifier(console)
    valid = eutils.validate_classifier(classifier)
    if not valid:
        console.write(f"{c.RED}Invalid classifier: {c.WHITE}{classifier}")
        return
    function_message = m.FunctionMessage('debug_envy()')
    function_message.set_target(Purpose.CLIENT)
    function_message.set_function('debug')
    send_to_clients(console, classifier, function_message)


def send_to_clients(console, classifier: str, function_message: m.FunctionMessage) -> None:
    """
    sends a single message to the server with a message.FunctionMessage within.
    the server will then send copies of the function message to any clients which meet the classifier
    :param console: reference to console making the call
    :param classifier: (str) classifier
    :param function_message: (networkUtils.message.FunctionMessage) A properly created FunctionMessage
    :return: Void
    """
    message = m.Message(f'Pass on: {function_message}')
    message.set_purpose(Purpose.PASS_ON)
    message.set_data(function_message.as_dict())
    message.set_message(classifier)
    console.add_to_send_queue(message)
