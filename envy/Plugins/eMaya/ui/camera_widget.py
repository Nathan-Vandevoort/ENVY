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

import sys
import os

e_maya_ui_path = os.path.dirname(__file__)

if e_maya_ui_path not in sys.path:
    sys.path.append(e_maya_ui_path)

import frame_range_widget as frame_range_wdt


class CameraWidget(QtWidgets.QWidget):

    def __init__(self):
        super(CameraWidget, self).__init__()

        self.setEnabled(False)

        self.icons_path = os.path.join(e_maya_ui_path, 'icons')

        self.renderable_camera_push_button = None
        self.camera_name_label = None
        self.frame_range_widget = None

        self.main_layout = None
        self.camera_group_box = None
        self.camera_h_box_layout = None

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_widgets(self) -> None:
        """Creates the widgets."""
        self.renderable_camera_push_button = QtWidgets.QPushButton()
        self.renderable_camera_push_button.setCheckable(True)
        self.renderable_camera_push_button.setFixedSize(26, 26)
        self.renderable_camera_push_button.setIcon(QtGui.QIcon(os.path.join(self.icons_path, 'video-camera-alt.png')))
        self.renderable_camera_push_button.setIconSize(QtCore.QSize(18, 18))
        self.renderable_camera_push_button.setStyleSheet('''
                            QPushButton {
                                background-color: rgb(45, 45, 45); 
                                border-radius: 5px; 
                            }

                            QPushButton:checked {
                                background-color: rgb(54, 103, 124); 
                                border: none;
                            }''')

        self.camera_name_label = QtWidgets.QLabel()
        self.camera_name_label.setMaximumWidth(400)
        self.camera_name_label.setEnabled(False)

        self.frame_range_widget = frame_range_wdt.FrameRangeWidget()

    def create_layouts(self) -> None:
        """Creates the layouts."""
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 0, 0, 0)
        self.main_layout.setSpacing(2)

        self.camera_group_box = QtWidgets.QGroupBox()
        self.camera_group_box.setFixedHeight(36)
        self.camera_group_box.setStyleSheet('QGroupBox {background-color: rgb(45, 45, 45); border-radius: 5px;}')
        self.main_layout.addWidget(self.camera_group_box)

        self.camera_h_box_layout = QtWidgets.QHBoxLayout()
        self.camera_h_box_layout.addWidget(self.renderable_camera_push_button)
        self.camera_h_box_layout.addWidget(self.camera_name_label)
        self.camera_h_box_layout.addStretch()
        self.camera_h_box_layout.addWidget(self.frame_range_widget)
        self.camera_h_box_layout.setContentsMargins(4, 4, 4, 4)
        self.camera_h_box_layout.setSpacing(4)
        self.camera_group_box.setLayout(self.camera_h_box_layout)

    def create_connections(self) -> None:
        """Creates the connections."""
        self.renderable_camera_push_button.toggled.connect(self.renderable_camera_push_button_toggled)

    def renderable_camera_push_button_toggled(self, checked: bool) -> None:
        """"""
        self.camera_name_label.setEnabled(checked)
        self.frame_range_widget.setEnabled(checked)

    def get_camera_name(self) -> str:
        """Gets the camera name."""
        camera_name = self.toolTip()

        return camera_name

    def get_start_frame(self) -> int:
        """Gets the start frame."""
        start_frame = self.frame_range_widget.get_start_frame()

        return start_frame

    def get_end_frame(self) -> int:
        """Gets the end frame."""
        end_frame = self.frame_range_widget.get_end_frame()

        return end_frame

    def is_renderable(self) -> bool:
        """Gets whether the camera is renderable."""
        renderable = self.renderable_camera_push_button.isChecked()

        return renderable

    def set_camera_name(self, name: str) -> None:
        """Sets the camera name."""
        self.camera_name_label.setText(name.split('|')[-1])
        self.setToolTip(name)

    def set_start_frame(self, frame: int) -> None:
        """Sets the start frame."""
        self.frame_range_widget.set_start_frame(frame)

    def set_end_frame(self, frame: int) -> None:
        """Sets the end frame."""
        self.frame_range_widget.set_end_frame(frame)

    def set_renderable(self, renderable: bool) -> None:
        """Sets the layer render as renderable."""
        self.renderable_camera_push_button.setChecked(renderable)

    def use_custom_frame_range(self) -> bool:
        """"""
        custom_time = self.frame_range_widget.use_custom_frame_range()

        return custom_time
