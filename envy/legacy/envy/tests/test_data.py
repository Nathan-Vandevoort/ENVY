import logging
from envy.lib.core.data import Client, Console, to_json, from_json, ClientStatus


logger = logging.getLogger(__name__)


def test_to_json():
    client_01 = Client('lab1-01', ClientStatus.IDLE, 15245, 48596, '192.168.1.1')
    as_json = to_json(client_01)
    logger.debug(f'{as_json=}')

    client_02 = from_json(Client, as_json)
    logger.debug(f'{client_02=}')

    assert client_01 == client_02


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_to_json()
