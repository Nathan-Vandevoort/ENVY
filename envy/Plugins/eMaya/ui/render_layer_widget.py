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


e_maya_path = 'Z:/Envy/__ENVYTEST__/plugins/eMaya/ui'

if e_maya_path not in sys.path:
    sys.path.append(e_maya_path)

import camera_widget as camera_wdt

import imp
imp.reload(camera_wdt)


class RenderLayerWidget(QtWidgets.QWidget):

    def __init__(self):
        super(RenderLayerWidget, self).__init__()
        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_widgets(self) -> None:
        """Creates the widgets."""
        self.expand_push_button = QtWidgets.QPushButton()
        self.expand_push_button.setFixedSize(16, 16)

        self.render_layer_name_label = QtWidgets.QLabel()
        self.render_layer_name_label.setEnabled(False)

        self.start_frame_spin_box = QtWidgets.QSpinBox()
        self.start_frame_spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.start_frame_spin_box.setFixedWidth(50)
        self.start_frame_spin_box.setReadOnly(True)

        self.end_frame_spin_box = QtWidgets.QSpinBox()
        self.end_frame_spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.end_frame_spin_box.setFixedWidth(50)
        self.end_frame_spin_box.setMaximum(10000)
        self.end_frame_spin_box.setReadOnly(True)

        self.renderable_render_layer_push_button = QtWidgets.QPushButton()
        self.renderable_render_layer_push_button.setCheckable(True)
        self.renderable_render_layer_push_button.setFixedSize(26, 26)
        self.renderable_render_layer_push_button.setIcon(QtGui.QIcon('C:/Users/Mauricio/Documents/maya/2024/prefs/icons/exit.png'))
        self.renderable_render_layer_push_button.setStyleSheet('''
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
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(2)

        self.render_layer_group_box = QtWidgets.QGroupBox()
        self.render_layer_group_box.setFixedHeight(36)
        self.render_layer_group_box.setStyleSheet(
            'QGroupBox {background-color: rgb(45, 45, 45); border-radius: 5px;}')
        self.main_layout.addWidget(self.render_layer_group_box)

        self.render_layer_h_box_layout = QtWidgets.QHBoxLayout()
        self.render_layer_h_box_layout.addWidget(self.expand_push_button)
        self.render_layer_h_box_layout.addWidget(self.render_layer_name_label)
        self.render_layer_h_box_layout.setContentsMargins(4, 4, 4, 4)
        self.render_layer_h_box_layout.setSpacing(4)
        self.render_layer_group_box.setLayout(self.render_layer_h_box_layout)

        self.render_frame_range_group_box = QtWidgets.QGroupBox()
        self.render_frame_range_group_box.setEnabled(False)
        self.render_frame_range_group_box.setFixedWidth(112)
        self.render_frame_range_group_box.setStyleSheet(
            'QGroupBox {background-color: rgb(65, 65, 65); border-radius: 5px;}')
        self.render_layer_h_box_layout.addWidget(self.render_frame_range_group_box)

        self.render_frame_range_h_box_layout = QtWidgets.QHBoxLayout()
        self.render_frame_range_h_box_layout.addWidget(self.start_frame_spin_box)
        self.render_frame_range_h_box_layout.addWidget(self.end_frame_spin_box)
        self.render_frame_range_h_box_layout.setContentsMargins(2, 0, 0, 0)
        self.render_frame_range_h_box_layout.setSpacing(2)
        self.render_frame_range_group_box.setLayout(self.render_frame_range_h_box_layout)

        self.render_layer_h_box_layout.addWidget(self.renderable_render_layer_push_button)

    def create_connections(self) -> None:
        """Creates the connections."""
        self.renderable_render_layer_push_button.toggled.connect(self.renderable_render_layer_push_button_toggled)

    def renderable_render_layer_push_button_toggled(self, checked) -> None:
        """"""
        self.render_layer_name_label.setEnabled(checked)
        self.render_frame_range_group_box.setEnabled(checked)

    def add_camera_widget(self, camera: str) -> camera_wdt.CameraWidget:
        """Adds a camera widget to the render layer widget."""
        camera_widget = camera_wdt.CameraWidget()
        camera_widget.set_camera_name(camera)
        self.main_layout.addWidget(camera_widget)

        return camera_widget

    def set_render_layer_name(self, name: str) -> None:
        """Sets the render layer name."""
        self.render_layer_name_label.setText(f'<b>Layer:</b> {name}')

    def set_start_frame(self, frame: int) -> None:
        """Sets the start frame."""
        self.start_frame_spin_box.setValue(frame)

    def set_end_frame(self, frame: int) -> None:
        """Sets the end frame."""
        self.end_frame_spin_box.setValue(frame)

    def set_renderable(self, renderable: bool) -> None:
        """Sets the layer render as renderable."""
        self.renderable_render_layer_push_button.setChecked(renderable)
