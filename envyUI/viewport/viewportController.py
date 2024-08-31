from PySide6.QtCore import QObject, Slot, Signal, QTimer
import time

class ViewportController(QObject):
    def __init__(self, scene):
        super().__init__()

        self.scene = scene

    def wait_until_scene_is_running(self):
        if self.scene.running is True:
            self.timer.stop()

    @Slot(tuple)
    def register_client(self, data):
        client = data[0]
        client_data = data[1]
        self.scene.add_computer(client, client_data)

    @Slot(str)
    def unregister_client(self, client: str):
        self.scene.remove_computer(client)

    @Slot(dict)
    def set_clients(self, clients: dict):
        while self.scene.running is False:
            time.sleep(.1)

        for client in clients:
            self.register_client((client, clients[client]))