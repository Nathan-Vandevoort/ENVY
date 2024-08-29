from PySide6.QtCore import QObject, Slot, Signal


class JobTreeController(QObject):

    def __init__(self, model):
        super().__init__()
        self.model = model

    @Slot(float)
    def mark_job_as_finished(self, job_id: float) -> None:  # these need to be casted from float to int
        self.model.mark_job_as_finished(int(job_id))


    @Slot(float)
    def sync_job(self, job_id: float) -> None:
        print('syncing job')
        self.model.job_tree.sync_job(int(job_id))