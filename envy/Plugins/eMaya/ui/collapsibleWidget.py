try:
    import PySide6.QtWidgets as QtWidgets
    import PySide6.QtCore as QtCore
    import PySide6.QtGui as QtGui
    from shiboken6 import wrapInstance
except ModuleNotFoundError:
    import PySide2.QtWidgets as QtWidgets
    import PySide2.QtCore as QtCore
    import PySide2.QtGui as QtGui
    from shiboken2 import wrapInstance

import sys
import os

class CollapsibleWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CollapsibleWidget, self).__init__(parent=parent)

        self.layout = QtWidgets.QVBoxLayout()

        self.toggle_button = QtWidgets.QToolButton()
        self.toggle_button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(QtCore.Qt.ArrowType.RightArrow)
        self.toggle_button.setText('Advanced Settings')
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)

        self.content_area_layout = QtWidgets.QVBoxLayout()
        self.content_area_layout.setSpacing(0)
        self.content_area_layout.setContentsMargins(0, 0, 0, 0)
        self.content_area = QtWidgets.QScrollArea()
        self.content_area.setStyleSheet('QScrollArea { border: none; }')
        self.content_area.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)

        self.animation_group = QtCore.QParallelAnimationGroup()

        self.animation = QtCore.QPropertyAnimation(self.content_area, b'maximumHeight')
        self.animation.setDuration(150)
        self.animation_group.addAnimation(self.animation)

        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 10, 0, 0)
        self.layout.addWidget(self.toggle_button)
        self.layout.addWidget(self.content_area)

        self.max_height = 200

        self.toggle_button.clicked.connect(self.toggle)
        self.setLayout(self.layout)

    def add_widget(self, widget):
        self.content_area_layout.addWidget(widget)
        self.content_area.setLayout(self.content_area_layout)

    def toggle(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(QtCore.Qt.ArrowType.DownArrow if checked else QtCore.Qt.ArrowType.RightArrow)
        self.animation.setStartValue(self.content_area.maximumHeight())
        self.animation.setEndValue(self.max_height if checked else 0)
        self.animation_group.start()

if __name__ == '__main__':
    class MainWindow(QtWidgets.QMainWindow):
        def __init__(self, event_loop=None):
            super().__init__()
            self.event_loop = event_loop
            self.widget = CollapsibleWidget()
            self.test = QtWidgets.QLabel()
            self.test.setText('poopoo')
            self.test2 = QtWidgets.QPushButton(text='potato')
            self.test3 = QtWidgets.QPushButton(text='orange')
            self.widget.add_widget(self.test)
            self.widget.add_widget(self.test2)
            self.widget.add_widget(self.test3)
            self.setCentralWidget(self.widget)

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())