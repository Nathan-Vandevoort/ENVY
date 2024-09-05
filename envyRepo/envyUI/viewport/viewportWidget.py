from PySide6.QtWidgets import QGraphicsView, QApplication, QMainWindow
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPainter
from envyRepo.envyUI.viewport.nodeScene import NodeScene
from envyRepo.envyUI.viewport.viewportController import ViewportController
import sys


class ViewportWidget(QGraphicsView):
    def __init__(self, parent=None, width=800, height=800):
        super().__init__(parent=parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.scene = NodeScene()
        self.scene.setSceneRect(0, 0, width, height)
        self.scene.start()
        self.controller = ViewportController(self.scene)
        self.setScene(self.scene)
        self.show()


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setBaseSize(1600, 1600)
            self.viewport_widget = ViewportWidget(parent=self)
            self.setCentralWidget(self.viewport_widget)


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())