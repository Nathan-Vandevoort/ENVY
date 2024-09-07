from PySide6.QtCore import QObject, Slot, Signal


class JobTreeController(QObject):

    def __init__(self, model):
        super().__init__()
        self.model = model

    @Slot(float)
    def mark_job_as_finished(self, job_id: float) -> None:  # these need to be casted from float to int
        self.model.finish_job(int(job_id))


    @Slot(float)
    def sync_job(self, job_id: float) -> None:
        self.model.sync_job(int(job_id))

    @Slot(tuple)
    def mark_task_as_started(self, data_tuple):
        task_id = data_tuple[0]
        computer = data_tuple[1]
        self.model.start_task(task_id, computer)

    @Slot(float)
    def mark_task_as_finished(self, task_id):
        self.model.finish_task(int(task_id))

    @Slot(float)
    def mark_allocation_as_finished(self, allocation_id):
        self.model.finish_allocation(int(allocation_id))

    @Slot(tuple)
    def mark_allocation_as_started(self, data_tuple):
        allocation_id = data_tuple[0]
        computer = data_tuple[1]
        self.model.start_allocation(computer, int(allocation_id))

    @Slot(int)
    def disconnected_with_server(self):
        pass

    @Slot(int)
    def connected_with_server(self):
        pass

    @Slot(tuple)
    def mark_task_as_failed(self, data_tuple):
        task_id = data_tuple[0]
        reason = data_tuple[1]
        self.model.fail_task(task_id, reason)

    @Slot(tuple)
    def update_task_progress(self, data_tuple):
        task_id = data_tuple[0]
        progress = data_tuple[1]
        self.model.update_task_progress(task_id, progress)