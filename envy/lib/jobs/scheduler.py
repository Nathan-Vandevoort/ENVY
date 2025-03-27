import asyncio
import logging
import sys

import anytree

import envy.lib.jobs.ingestor as ingestor
from envy.lib.db import db
from envy.lib.jobs.enums import Status
from envy.lib.jobs.jobTreeAbstractItemModel import JobTreeItemModel as JobTree

SRV = sys.modules.get('Server_Functions')

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, server, event_loop):
        self.server = server

        self.event_loop = asyncio.get_running_loop()
        self.db = db.DB()
        self.ingestor = ingestor.Ingestor(self)
        self.job_tree = JobTree()
        self.scheduler_tasks = []
        self.clients = server.clients

    async def issue_task(self, computer_name: str) -> bool:
        logger.debug(f'Scheduler: allocating tasks for {computer_name}')
        for allocation in self.job_tree.pick_allocation():
            if allocation is None:
                return False
            if self.check_allocation(allocation, computer=computer_name) is True:
                logger.debug(f'Scheduler: Allocation ({allocation.name}) chosen for {computer_name}')
                self.clients[computer_name]['Job'] = allocation.parent.name
                self.clients[computer_name]['Allocation'] = allocation.name
                self.job_tree.start_allocation(computer_name, allocation)
                message = self.job_tree.allocation_as_message(allocation)
                await SRV.mark_allocation_as_started(self.server, allocation.name, computer_name)
                await SRV.send_to_client(self.server, computer_name, message)
                return True

    async def finish_job(self, job_id: int, stop_workers: bool = False):
        logger.info(f'Scheduler: Finishing Job {job_id}')

        if stop_workers is True:
            for client in self.clients:
                if self.clients[client]['Job'] == job_id:
                    logger.debug(f'Scheduler: stopping {client}')
                    await SRV.stop_client(self.server, client)

        self.job_tree.finish_job(job_id)

    async def finish_task(self, task_id: int):
        logger.info(f'Scheduler: Finishing task {task_id}')
        self.job_tree.finish_task(task_id=task_id)

    async def start_task(self, task_id: int, computer: str):
        logger.info(f'Scheduler: {computer} started task {task_id}')
        self.job_tree.start_task(task_id, computer)

    async def finish_allocation(self, allocation_id: int, stop_workers: bool = False):
        logger.info(f'Scheduler: finishing allocation {allocation_id}')

        if stop_workers is True:
            for client in self.clients:
                if self.clients[client]['Allocation'] == allocation_id:
                    logger.debug(f'Scheduler: stopping {client}')
                    await SRV.stop_client(self.server, client)

        self.job_tree.finish_allocation(allocation_id)

    async def fail_task(self, task_id: int, reason: str):
        logger.info(f'Scheduler: failing task {task_id} for reason {reason}')
        self.job_tree.fail_task(task_id, reason)

    async def fail_allocation(self, allocation_id: int, reason: str):
        logger.info(f'Scheduler: Failing allocation {allocation_id} for reason {reason}')
        self.job_tree.fail_allocation(allocation_id, reason)

    def check_allocation(self, allocation: anytree.Node | int, computer: str = None) -> bool:
        logger.debug(f'checking allocation {allocation} with computer {computer}')
        if isinstance(allocation, int):
            allocation = self.job_tree.get_allocation(allocation)
        if allocation is None:
            return False
        if allocation.status == Status.DIRTY or allocation.status == Status.FAILED:
            return False
        if allocation.computer in self.clients:
            if allocation.computer == computer:
                logger.info(f'Scheduler: Envy Instance on {computer} must have been restarted.')
                return True
            logger.debug(f'Scheduler: {allocation} is already being worked on cannot be allocated')
            return False
        return True

    async def sync_job(self, job_id: int):
        self.job_tree.sync_job(job_id)
        await SRV.console_sync_job(self.server, job_id)

    async def start(self):
        logger.debug("Starting...")
        self.db.start()
        self.job_tree.set_db(self.db)
        active_allocations = self.job_tree.build_from_db()

        logger.debug(f'Scheduler: Active Task_Allocations: {active_allocations}')
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
                    continue
