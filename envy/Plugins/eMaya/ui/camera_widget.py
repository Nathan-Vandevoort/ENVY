"""
========================================================================================================================
Name: camera_widget.py
Author: Mauricio Gonzalez Soto
========================================================================================================================
"""
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


class CameraWidget(QtWidgets.QWidget):

    def __init__(self):
        super(CameraWidget, self).__init__()

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_widgets(self) -> None:
        """Creates the widgets."""
        self.camera_label = QtWidgets.QLabel()

        self.renderable_camera_push_button = QtWidgets.QPushButton()
        self.renderable_camera_push_button.setCheckable(True)
        self.renderable_camera_push_button.setFixedSize(26, 26)
        self.renderable_camera_push_button.setIcon(
            QtGui.QIcon('C:/Users/Mauricio/Documents/maya/2024/prefs/icons/exit.png'))
        self.renderable_camera_push_button.setStyleSheet('''
                    QPushButton {
                        background-color: rgb(45, 45, 45); 
                        border-radius: 5px; 
                    }

                    QPushButton:checked {
                        background-color: rgb(54, 103, 124); 
                        border: none;
                    }''')

    def create_layouts(self) -> None:
        """Creates the layouts."""
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 0, 0, 0)
        self.main_layout.setSpacing(2)

        self.camera_group_box = QtWidgets.QGroupBox()
        self.camera_group_box.setFixedHeight(30)
        self.camera_group_box.setStyleSheet(
            'QGroupBox {background-color: rgb(55, 55, 55); border-radius: 5px;}')
        self.main_layout.addWidget(self.camera_group_box)

        self.camera_h_box_layout = QtWidgets.QHBoxLayout()
        self.camera_h_box_layout.addWidget(self.camera_label)
        self.camera_h_box_layout.addWidget(self.renderable_camera_push_button)
        self.camera_h_box_layout.setContentsMargins(24, 0, 4, 0)
        self.camera_h_box_layout.setSpacing(4)
        self.camera_group_box.setLayout(self.camera_h_box_layout)

    def create_connections(self) -> None:
        """Creates the connections."""

    def set_camera_name(self, name: str) -> None:
        """Sets the camera name."""
        self.camera_label.setText(f'<b>Camera:</b> {name}')

    def set_renderable(self, renderable: bool) -> None:
        """Sets the layer render as renderable."""
        self.renderable_camera_push_button.setChecked(renderable)
