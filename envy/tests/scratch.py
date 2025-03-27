import asyncio
import socket
import websockets

from envy.lib.utils.utils import get_hash
from envy.lib.db.utils import get_server_ip

ip = socket.gethostbyname(socket.gethostname())

print(get_server_ip())
uri = f"ws://{get_server_ip()}:3720/client"
headers = {
    'passkey': get_hash(),
    'name': 'host',
    'job': None,
    'task': None,
}


async def run():
    websocket = await websockets.connect(uri, extra_headers=headers)


asyncio.run(run())

print(ip)
