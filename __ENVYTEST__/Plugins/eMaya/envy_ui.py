"""
========================================================================================================================
Name: envy_ui.py
========================================================================================================================
"""
try:
    import PySide2.QtWidgets as QtWidgets
    import PySide2.QtCore as QtCore
    import PySide2.QtGui as QtGui
    from shiboken2 import wrapInstance
except ModuleNotFoundError:
    import PySide6.QtWidgets as QtWidgets
    import PySide6.QwCore as QtCore
    import PySide6.QtGui as QtGui
    from shiboken6 import wrapInstance

import maya.cmds as cmds
import maya.OpenMayaUI as omui

import sys

envy_path = 'Z:/Envy/__ENVYTEST__/Plugins/eMaya'

if envy_path not in sys.path:
    sys.path.append(envy_path)


import maya_to_envy


def maya_main_window() -> any:
    """Gets the Maya main window widget as a Python object."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    main_window = wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

    return main_window


class EnvyUI(QtWidgets.QDialog):

    def __init__(self, parent=maya_main_window()):
        """"""
        super(EnvyUI, self).__init__(parent)

        self.setWindowTitle('Envy')
        
        self.main_layout = None
        
        self.camera_header_list_group_box = None
        self.cameras_header_list_v_box_layout = None
        self.cameras_list_v_box_layout = None
        self.camera_name_label = None
        self.custom_frames_label = None
        self.start_frame_label = None
        self.end_frame_label = None

        self.render_push_button = None

        self.create_widgets()
        self.create_layouts()
        self.create_connections()
        self.create_camera_item_widgets()

    def create_widgets(self) -> None:
        """Creates the widgets."""
        self.camera_name_label = QtWidgets.QLabel('Camera')
        self.custom_frames_label = QtWidgets.QLabel('Custom Frames')
        self.start_frame_label = QtWidgets.QLabel('Start Frame')
        self.end_frame_label = QtWidgets.QLabel('End Frame')

        self.render_push_button = QtWidgets.QPushButton('Render')

    def create_layouts(self) -> None:
        """Creates the layouts."""
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.setSpacing(2)
        
        self.camera_header_list_group_box = QtWidgets.QGroupBox()
        self.camera_header_list_group_box.setContentsMargins(0, 0, 0, 0)
        self.camera_header_list_group_box.setFixedHeight(25)
        self.main_layout.addWidget(self.camera_header_list_group_box)
        
        self.cameras_header_list_v_box_layout = QtWidgets.QHBoxLayout()
        self.cameras_header_list_v_box_layout.addWidget(self.camera_name_label)
        self.cameras_header_list_v_box_layout.addWidget(self.custom_frames_label)
        self.cameras_header_list_v_box_layout.addWidget(self.start_frame_label)
        self.cameras_header_list_v_box_layout.addWidget(self.end_frame_label)
        self.cameras_header_list_v_box_layout.setContentsMargins(2, 2, 2, 2)
        self.cameras_header_list_v_box_layout.setSpacing(2)
        self.camera_header_list_group_box.setLayout(self.cameras_header_list_v_box_layout)
        
        self.cameras_list_v_box_layout = QtWidgets.QVBoxLayout()
        self.cameras_list_v_box_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.addLayout(self.cameras_list_v_box_layout)

        self.main_layout.addWidget(self.render_push_button)

    def create_connections(self) -> None:
        """Creates the connections."""
        self.render_push_button.clicked.connect(self.render)
        
    def create_camera_item_widgets(self) -> None:
        """"""
        cameras = cmds.ls(cameras=True, long=True)
        
        for camera in cameras:
            if not cmds.getAttr(f'{camera}.orthographic'):
                camera_item_widget = CameraItemWidget(camera)
                self.cameras_list_v_box_layout.addWidget(camera_item_widget)

    @staticmethod
    def render():
        """Sets the Maya scene to Envy."""
        envy = maya_to_envy.MayaToEnvy()
        envy.export_to_envy(envy.get_cameras()[0], envy.get_render_layers()[0])


class CameraItemWidget(QtWidgets.QGroupBox):

    def __init__(self, camera):
        super(CameraItemWidget, self).__init__()
        
        self.setFixedHeight(25)
    
        self.camera = camera
        self.envy = maya_to_envy.MayaToEnvy()

        self.main_layout = None
        
        self.use_camera_check_box = None
        self.camera_name_label = None
        self.use_custom_frames_check_box = None
        self.start_frame_spin_box = None
        self.end_frame_spin_box = None

        self.create_widgets()
        self.create_layouts()
        self.create_connections()
        
    def create_widgets(self) -> None:
        """"""
        self.use_camera_check_box = QtWidgets.QCheckBox()
        self.use_camera_check_box.setChecked(True)
        
        self.camera_name_label = QtWidgets.QLabel(self.camera)
        self.camera_name_label.setFixedWidth(150)
        
        self.use_custom_frames_check_box = QtWidgets.QCheckBox()

        self.start_frame_spin_box = QtWidgets.QSpinBox()
        self.start_frame_spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.start_frame_spin_box.setEnabled(False)
        self.start_frame_spin_box.setFixedWidth(75)
        self.start_frame_spin_box.setValue(self.envy.get_start_frame())

        self.end_frame_spin_box = QtWidgets.QSpinBox()
        self.end_frame_spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.end_frame_spin_box.setEnabled(False)
        self.end_frame_spin_box.setFixedWidth(75)
        self.end_frame_spin_box.setValue(self.envy.get_end_frame())

    def create_layouts(self) -> None:
        """"""
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.use_camera_check_box)
        self.main_layout.addWidget(self.camera_name_label)
        self.main_layout.addWidget(self.use_custom_frames_check_box)
        self.main_layout.addWidget(self.start_frame_spin_box)
        self.main_layout.addWidget(self.end_frame_spin_box)
        self.main_layout.addStretch()

    def create_connections(self) -> None:
        """"""
        self.use_camera_check_box.toggled.connect(self.enabled_widgets)
        self.use_custom_frames_check_box.toggled.connect(self.enabled_widgets)

    def enabled_widgets(self) -> None:
        """"""
        use_camera = self.use_camera_check_box.isChecked()
        use_custom_frames_check_box = self.use_custom_frames_check_box.isChecked()

        self.use_custom_frames_check_box.setEnabled(use_camera)

        self.start_frame_spin_box.setEnabled(use_camera and use_custom_frames_check_box)
        self.end_frame_spin_box.setEnabled(use_camera and use_custom_frames_check_box)


try:
    ui.close()
    ui.deleteLater()
except:
    pass
    
ui = EnvyUI()
ui.show()
