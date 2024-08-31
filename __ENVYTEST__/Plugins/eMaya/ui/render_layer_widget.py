"""
========================================================================================================================
Name: render_layer_widget.py
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
e_maya_path = os.path.dirname(e_maya_ui_path)

if e_maya_path not in sys.path:
    sys.path.append(e_maya_path)

if e_maya_ui_path not in sys.path:
    sys.path.append(e_maya_ui_path)

import frame_range_widget as frame_range_wdt
import camera_widget as camera_wdt
import maya_to_envy

import imp
imp.reload(camera_wdt)
imp.reload(frame_range_wdt)


class RenderLayerWidget(QtWidgets.QWidget):

    def __init__(self):
        """"""
        super(RenderLayerWidget, self).__init__()

        self.icons_path = os.path.join(e_maya_ui_path, 'icons')
        self.maya_to_envy = maya_to_envy.MayaToEnvy()

        self.renderable_render_layer_push_button = None
        self.render_layer_name_label = None
        self.frame_range_widget = None

        self.main_layout = None
        self.render_layer_group_box = None
        self.render_layer_h_box_layout = None
        self.cameras_widgets_widget = None
        self.cameras_widgets_v_box_layout = None

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_widgets(self) -> None:
        """Creates the widgets."""
        self.renderable_render_layer_push_button = QtWidgets.QPushButton()
        self.renderable_render_layer_push_button.setCheckable(True)
        self.renderable_render_layer_push_button.setFixedSize(26, 26)
        self.renderable_render_layer_push_button.setIcon(QtGui.QIcon(os.path.join(self.icons_path, 'clapperboard.png')))
        self.renderable_render_layer_push_button.setIconSize(QtCore.QSize(18, 18))
        self.renderable_render_layer_push_button.setStyleSheet('''
                    QPushButton {
                        background-color: rgb(45, 45, 45); 
                        border-radius: 5px; 
                    }

                    QPushButton:checked {
                        background-color: rgb(54, 103, 124); 
                        border: none;
                    }''')

        self.render_layer_name_label = QtWidgets.QLabel()
        self.render_layer_name_label.setEnabled(False)

        self.frame_range_widget = frame_range_wdt.FrameRangeWidget()

    def create_layouts(self) -> None:
        """Creates the layouts."""
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(2)

        self.render_layer_group_box = QtWidgets.QGroupBox()
        self.render_layer_group_box.setFixedHeight(36)
        self.render_layer_group_box.setStyleSheet(
            'QGroupBox {background-color: rgb(45, 45, 45); border-radius: 5px;}')
        self.main_layout.addWidget(self.render_layer_group_box)

        self.render_layer_h_box_layout = QtWidgets.QHBoxLayout()
        self.render_layer_h_box_layout.addWidget(self.renderable_render_layer_push_button)
        self.render_layer_h_box_layout.addWidget(self.render_layer_name_label)
        self.render_layer_h_box_layout.addStretch()
        self.render_layer_h_box_layout.addWidget(self.frame_range_widget)
        self.render_layer_h_box_layout.setContentsMargins(4, 4, 4, 4)
        self.render_layer_h_box_layout.setSpacing(4)
        self.render_layer_group_box.setLayout(self.render_layer_h_box_layout)

        self.cameras_widgets_widget = QtWidgets.QWidget()
        self.main_layout.addWidget(self.cameras_widgets_widget)

        self.cameras_widgets_v_box_layout = QtWidgets.QVBoxLayout()
        self.cameras_widgets_v_box_layout.setContentsMargins(0, 0, 0, 0)
        self.cameras_widgets_v_box_layout.setSpacing(2)
        self.cameras_widgets_widget.setLayout(self.cameras_widgets_v_box_layout)

    def create_connections(self) -> None:
        """Creates the connections."""
        self.renderable_render_layer_push_button.toggled.connect(self.renderable_render_layer_push_button_toggled)

    def renderable_render_layer_push_button_toggled(self, checked) -> None:
        """"""
        self.render_layer_name_label.setEnabled(checked)
        self.frame_range_widget.setEnabled(checked)

        for camera_widget in self.get_camera_widgets():
            camera_widget.setEnabled(checked)

    def add_camera_widget(self, camera: str) -> camera_wdt.CameraWidget:
        """Adds a camera widget to the render layer widget."""
        camera_widget = camera_wdt.CameraWidget()
        camera_widget.set_camera_name(camera)
        camera_widget.set_start_frame(self.get_start_frame())
        camera_widget.set_end_frame(self.get_end_frame())
        self.cameras_widgets_v_box_layout.addWidget(camera_widget)

        return camera_widget

    def create_camera_widgets(self) -> None:
        """Creates cameras widgets."""
        for camera in self.maya_to_envy.get_cameras_from_render_layer(self.get_render_layer_name()):
            self.add_camera_widget(camera)

    def is_renderable(self) -> bool:
        """Gets whether the camera is renderable."""
        renderable = self.renderable_render_layer_push_button.isChecked()

        return renderable

    def get_camera_widgets(self) -> list:
        """Gets the camera widgets."""
        camera_widgets = []

        for widget in self.cameras_widgets_widget.children():
            if type(widget) is camera_wdt.CameraWidget:
                camera_widgets.append(widget)

        return camera_widgets

    def get_render_layer_name(self) -> str:
        """Gets the render layer name."""
        render_layer_name = self.render_layer_name_label.text()

        return render_layer_name

    def get_start_frame(self) -> int:
        """Gets the start frame."""
        start_frame = self.frame_range_widget.get_start_frame()

        return start_frame

    def get_end_frame(self) -> int:
        """Gets the end frame."""
        end_frame = self.frame_range_widget.get_end_frame()

        return end_frame

    def set_render_layer_name(self, name: str) -> None:
        """Sets the render layer name."""
        self.render_layer_name_label.setText(name)

    def set_start_frame(self, frame: int) -> None:
        """Sets the start frame."""
        self.frame_range_widget.set_start_frame(frame)

    def set_end_frame(self, frame: int) -> None:
        """Sets the end frame."""
        self.frame_range_widget.set_end_frame(frame)

    def set_renderable(self, renderable: bool) -> None:
        """Sets the layer render as renderable."""
        self.renderable_render_layer_push_button.setChecked(renderable)

    def use_custom_frame_range(self) -> bool:
        """"""
        custom_time = self.frame_range_widget.use_custom_frame_range()

        return custom_time
