import user_config, sys, json
sys.path.append(user_config.Config.REPOPATH)
from networkUtils import message as m
from networkUtils.purpose import Purpose


async def send_to_console(server, console: str, message: m.Message | m.FunctionMessage) -> None:
    """
    send a networkUtils.message object to a console
    :param server: reference to server calling the function
    :param console: (str) name of console to send message to
    :param message: networkUtils.message object to send to client
    :return: Void
    """
    server.logger.debug(f'sending message: {message} to console: {console}')
    ws = server.consoles[console]['Socket']
    encoded_message = message.encode()
    await ws.send(encoded_message)


async def send_to_client(server, client: str, message: m.Message | m.FunctionMessage) -> None:
    """
    Send a networkUtils.message object to a client
    :param server: reference to server calling the function
    :param client: (str) name of client to send message to
    :param message: networkUtils.message object to send to client
    :return: Void
    """
    server.logger.debug(f'sending {message} to {client}')
    ws = server.clients[client]['Socket']
    json_message = message.encode()
    await ws.send(json_message)


async def send_attribute_to_client(server, client: str, attribute: str, buffer_name: str) -> None:
    """
    Sends the value of any attribute on the server object to any client
    :param server: reference to server calling the function
    :param client: (str) name of client to send message to
    :param attribute: (str) name of attribute to send
    :param buffer_name: (str) name of buffer on client you want to fill
    :return: Void
    """
    attribute = getattr(server, attribute)
    message = m.FunctionMessage(f'send_attribute_to_client(): {attribute}')
    message.set_purpose(Purpose.FUNCTION_MESSAGE)
    message.set_target(Purpose.CLIENT)
    message.set_function('fill_buffer')
    message.format_arguments(buffer_name, attribute)
    message.set_name(message.as_function())
    await send_to_client(server, client, message)


async def send_clients_to_console(server, target_consoles: str | list = None) -> None:
    """
    Send all currently connected clients to a particular console or a list of consoles
    :param server: reference to server calling the function
    :param target_consoles: (str) or (list) name of consoles to send to
    :return: Void
    """
    if isinstance(target_consoles, str):
        target_consoles = [target_consoles]

    if not target_consoles:
        target_consoles = list(server.consoles)

    clients = server.clients
    clients = {k: {k2: v2 for k2, v2 in v.items() if k2 != 'Socket'} for k, v in clients.items()}
    buffer_name = 'clients_buffer'

    server.logger.debug(f'sending (clients) to console: {target_consoles}')
    for console in target_consoles:
        message = m.FunctionMessage(f'send_clients_to_console()')
        message.set_purpose(Purpose.FUNCTION_MESSAGE)
        message.set_target(Purpose.CONSOLE)
        message.set_function('fill_buffer')
        message.format_arguments(buffer_name, data=clients)
        message.set_name(message.as_function())
        await send_to_console(server, console, message)


async def send_attribute_to_console(server, attribute: str, buffer_name: str, target_consoles: str | list = None) -> None:
    """
        Sends the value of any attribute on the server object to any client
        :param server: reference to server calling the function
        :param attribute: (str) name of attribute to send
        :param buffer_name: (str) name of buffer on console you want to fill
        :param target_consoles: (str) | (list) of console names
        :return: Void
        """
    if isinstance(target_consoles, str):
        target_consoles = [target_consoles]

    if not target_consoles:
        target_consoles = list(server.consoles)

    server.logger.debug(f'sending ({attribute}) to console: {target_consoles}')
    attribute = getattr(server, attribute)
    message = m.FunctionMessage(f'set server name')
    message.set_purpose(Purpose.FUNCTION_MESSAGE)
    message.set_target(Purpose.CONSOLE)
    message.set_function('fill_buffer')
    message.format_arguments(buffer_name, attribute)
    message.set_name(message.as_function())
    for console in target_consoles:
        await send_to_console(server, console, message)


async def send_to_consoles(server, message: m.Message | m.FunctionMessage) -> None:
    """
    sends a message to every console connected to the server
    :param server: a reference to the server object calling
    :param message: (networkUtils.message.Message) | (networkUtils.message.FunctionMessage)
    :return: Void
    """
    for console in server.consoles:
        try:
            await send_to_console(server, console, message)
        except KeyError:
            continue


async def send_to_clients(server, clients: list, message: m.Message | m.FunctionMessage) -> None:
    """
    sends a message to every client connected to the server
    :param server: reference to the server making the function call
    :param clients: list of client names to send message to
    :param message: (networkUtils.message.Message) | (networkUtils.message.FunctionMessage)
    :return: Void
    """
    for client in clients:
        await send_to_client(server, client, message)