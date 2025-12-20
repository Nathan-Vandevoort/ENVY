import logging

import tests
from envy import api

logger = logging.getLogger(__name__)


def test_get_plugin_names() -> None:
    plugins = api.get_plugins()
    logger.info(f"plugins: {plugins}")


def test_sandbox() -> None:
    plugin = api.get_plugin_from_name('example')
    if not plugin:
        return
    instance = plugin()


if __name__ == '__main__':
    tests.init()
    test_sandbox()
