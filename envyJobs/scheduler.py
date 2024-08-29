import logging
from envyLib.envy_utils import DummyLogger
from envyJobs.enums import Status
import asyncio
import envyJobs.ingestor as ingestor
from envyJobs.jobTree import JobTree
import sys
from envyDB import db
import anytree
SRV = sys.modules.get('Server_Functions')


class Scheduler:
    def __init__(self, server, event_loop, logger: logging.Logger = None):
        self.server = server
        self.logger = logger or DummyLogger()

        self.event_loop = event_loop
        self.db = db.DB(logger=logger)
        self.ingestor = ingestor.Ingestor(self, logger=logger)
        self.job_tree = JobTree(logger=logger)
        self.scheduler_tasks = []
        self.clients = server.clients

    async def issue_task(self, computer_name: str) -> bool:
        self.logger.debug(f'Scheduler: allocating tasks for {computer_name}')
        for allocation in self.job_tree.pick_allocation():
            if allocation is None:
                self.logger.debug('Scheduler: No more allocations to issue')
                return False
            if self.check_allocation(allocation, computer=computer_name) is True:
                self.logger.debug(f'Scheduler: Allocation ({allocation.name}) chosen for {computer_name}')
                self.clients[computer_name]['Job'] = allocation.parent.name
                self.clients[computer_name]['Allocation'] = allocation.name
                self.job_tree.start_allocation(computer_name, allocation)
                message = self.job_tree.allocation_as_message(allocation)
                await SRV.send_to_client(self.server, computer_name, message)
                return True

    def finish_job(self, job_id: int):
        self.logger.info(f'Scheduler: Finishing Job {job_id}')
        self.job_tree.finish_job(job_id)

    def finish_task(self, task_id: int):
        self.logger.info(f'Scheduler: Finishing task {task_id}')
        self.job_tree.finish_task(task_id=task_id)

    def start_task(self, task_id: int, computer: str):
        self.logger.info(f'Scheduler: {computer} started task {task_id}')
        self.job_tree.start_task(task_id, computer)

    def finish_allocation(self, allocation_id: int):
        self.logger.info(f'Scheduler: finishing allocation {allocation_id}')
        self.job_tree.finish_allocation(allocation_id)

    def check_allocation(self, allocation: anytree.Node | int, computer: str = None) -> bool:
        self.logger.debug(f'checking allocation {allocation} with computer {computer}')
        if isinstance(allocation, int):
            allocation = self.job_tree.get_allocation(allocation)
        if allocation is None:
            self.logger.debug(f'Scheduler: {allocation} is None cannot be allocated')
            return False
        if allocation.status == Status.DIRTY:
            return False
        if allocation.computer in self.clients:
            if allocation.computer == computer:
                self.logger.info(f'Scheduler: Envy Instance on {computer} must have been restarted.')
                return True
            self.logger.debug(f'Scheduler: {allocation} is already being worked on cannot be allocated')
            return False
        return True

    async def sync_job(self, job_id: int):
        self.job_tree.sync_job(job_id)
        await SRV.console_sync_job(self.server, job_id)

    async def start(self):
        self.logger.debug("Scheduler: Started")
        self.db.start()
        self.job_tree.set_db(self.db)
        active_allocations = self.job_tree.build_from_db()

        self.logger.debug(f'Scheduler: Active Task_Allocations: {active_allocations}')
        if active_allocations is not None:
            for allocation in active_allocations:
                status = self.check_allocation(allocation)
                if status is True:
                    self.job_tree.reset_allocation(allocation)

        self.ingestor.set_db(self.db)
        ingestor_task = self.event_loop.create_task(self.ingestor.start())
        ingestor_task.set_name('ingestor.start()')
        self.scheduler_tasks.append(ingestor_task)

        while True:
            await asyncio.sleep(2)
            if self.job_tree.number_of_jobs == 0:
                continue

            for client in self.clients:
                if self.clients[client]['Status'] != Status.IDLE:
                    continue
                success = await self.issue_task(client)
                if not success:
                    self.logger.debug('Scheduler: Failed to issue allocations')


if __name__ == '__main__':
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    loop = asyncio.new_event_loop()
    sched = Scheduler(loop, logger=logger)
    sched.start()
    loop.run_forever()
