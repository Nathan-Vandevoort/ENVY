import prep_env  # this is important to prepare the virtual environment
import asyncio
import logging

from envyCore.envy import Envy

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

loop = asyncio.new_event_loop()
envy = Envy(loop, logger=logger)
envy_task = loop.create_task(envy.run())
loop.run_forever()
