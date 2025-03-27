import typing
import asyncio
import logging
import traceback


logger = logging.getLogger(__name__)


class TaskRunner:

    def __init__(self):
        self._tasks: typing.Set[asyncio.Task] = set()
        self.check_interval = 2
        self._suppress_error_list = []

        try:
            self.event_loop = asyncio.get_running_loop()
        except RuntimeError:
            self.event_loop = asyncio.get_event_loop()

        self.exit_callback: typing.Callable = None
        self.running = False

        # Flags
        self.stop_loop_on_task_failure = False

    def suppress_error(self, e: type[Exception]) -> None:
        self._suppress_error_list.append(e)

    def create_task(self, task: asyncio.coroutines, name: str, callback: typing.Callable = None) -> None:
        new_task = self.event_loop.create_task(task, name=name)
        logger.debug(f'Created task: {name}')
        if callback:
            new_task.add_done_callback(callback)
            logger.debug(f'{name}: registered callback')
        self._tasks.add(new_task)

    def remove_task(self, task: asyncio.Task) -> None:
        task.cancel()
        self._tasks.remove(task)
        logger.debug(f'Removed task: {task.get_name()}')

    async def _check_tasks(self) -> None:
        while self.running:
            for task in set(self._tasks):
                if not task.done():
                    continue
                if e := task.exception():
                    if not isinstance(e, tuple(self._suppress_error_list)):
                        logger.error(f'Error in task {task.get_name()}: ', exc_info=e)
                    self.stop()
                else:
                    logger.debug(f'{task.get_name()} finished.')
                    self.remove_task(task)
            await asyncio.sleep(self.check_interval)

    def start(self):
        self.create_task(self._check_tasks(), 'TaskRunner', callback=self.stop)
        self.running = True

        if not self.event_loop.is_running():
            self.event_loop.run_forever()

    def stop(self, *args):
        self.running = False
        remove_list = []
        for task in self._tasks:
            task.cancel()
            remove_list.append(task)
            logger.debug(f'Cancelled task: {task.get_name()}')
        [self.remove_task(task) for task in remove_list]

        # TODO: Consider if this should be behavior of this class or implemented in a callback.
        if self.stop_loop_on_task_failure:
            self.event_loop.stop()
