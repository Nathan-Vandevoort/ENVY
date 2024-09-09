"""
========================================================================================================================
Name: envy_ui.py
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

import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
import maya.cmds as cmds

from functools import partial
import sys
import os

e_maya_ui_path = os.path.dirname(__file__)
e_maya_path = os.path.dirname(e_maya_ui_path)

if e_maya_path not in sys.path:
    sys.path.append(e_maya_path)

if e_maya_ui_path not in sys.path:
    sys.path.append(e_maya_ui_path)

import render_layer_widget as render_layer_wdt
import maya_to_envy
import advanced_settings_widget

import imp
imp.reload(render_layer_wdt)
imp.reload(maya_to_envy)


def maya_main_window() -> any:
    """Gets the Maya main window widget as a Python object."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    main_window = wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

    return main_window


class EnvyUI(QtWidgets.QDialog):
    WINDOW_NAME = 'Envy'
    WINDOW_TITLE = 'EnvyUI'

    window_instance = None

    def __init__(self, parent=maya_main_window()):
        """"""
        super(EnvyUI, self).__init__(parent)
        self.geometry = None

        self.maya_to_envy = maya_to_envy.MayaToEnvy()

        self.start_frame_spin_box = None
        self.end_frame_spin_box = None
        self.allocation_spin_box = None
        self.advanced_settings_widget = None
        self.render_push_button = None

        self.main_layout = None
        self.main_left_v_box_layout = None
        self.layer_renders_group_box = None
        self.layer_renders_v_box_layout = None
        self.main_right_v_box_layout = None
        self.render_settings_group_box = None
        self.render_settings_form_layout = None

        self.script_jobs = []

        # QDialog settings.
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(50, 50, 50))

        self.setAutoFillBackground(True)
        self.setObjectName(self.WINDOW_TITLE)
        self.setPalette(palette)
        self.setWindowTitle(self.WINDOW_NAME)

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    @classmethod
    def show_window(cls) -> None:
        """Shows the window."""
        if not cls.window_instance:
            cls.window_instance = EnvyUI()

        if cls.window_instance.isHidden():
            cls.window_instance.show()
        else:
            cls.window_instance.raise_()
            cls.window_instance.activateWindow()

    def create_widgets(self) -> None:
        """Creates the widgets."""
        self.start_frame_spin_box = QtWidgets.QSpinBox()
        self.start_frame_spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.start_frame_spin_box.setFixedSize(75, 20)
        self.start_frame_spin_box.setStyleSheet('''
                    QSpinBox {
                        background-color: rgb(40, 40, 40); 
                        border-radius: 5px;
                    }''')

        self.end_frame_spin_box = QtWidgets.QSpinBox()
        self.end_frame_spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.end_frame_spin_box.setFixedSize(75, 20)
        self.end_frame_spin_box.setMaximum(10000)
        self.end_frame_spin_box.setStyleSheet('''
                    QSpinBox {
                        background-color: rgb(40, 40, 40); 
                        border-radius: 5px;
                    }''')

        self.allocation_spin_box = QtWidgets.QSpinBox()
        self.allocation_spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.allocation_spin_box.setFixedSize(75, 20)
        self.allocation_spin_box.setMaximum(self.end_frame_spin_box.value() - self.start_frame_spin_box.value())
        self.allocation_spin_box.setMinimum(1)
        self.allocation_spin_box.setStyleSheet('''
                    QSpinBox {
                        background-color: rgb(40, 40, 40); 
                        border-radius: 5px;
                    }''')

        self.advanced_settings_widget = advanced_settings_widget.AdvancedSettingsWidget()

        self.render_push_button = QtWidgets.QPushButton('Render')

        self.restart_button = QtWidgets.QPushButton('Restart')

    def create_layouts(self) -> None:
        """Creates the layouts."""
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.setSpacing(2)

        self.main_left_v_box_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addLayout(self.main_left_v_box_layout)

        self.layer_renders_group_box = QtWidgets.QGroupBox()
        self.layer_renders_group_box.setStyleSheet('QGroupBox {background-color: rgb(30, 30, 30); border-radius: 5px;}')
        self.main_left_v_box_layout.addWidget(self.layer_renders_group_box)

        self.layer_renders_v_box_layout = QtWidgets.QVBoxLayout()
        self.layer_renders_v_box_layout.setAlignment(QtCore.Qt.AlignTop)
        self.layer_renders_v_box_layout.setContentsMargins(4, 4, 4, 4)
        self.layer_renders_v_box_layout.setSpacing(2)
        self.layer_renders_group_box.setLayout(self.layer_renders_v_box_layout)

        self.main_right_v_box_layout = QtWidgets.QVBoxLayout()
        self.main_right_v_box_layout.setAlignment(QtCore.Qt.AlignTop)
        self.main_layout.addLayout(self.main_right_v_box_layout)

        self.render_settings_group_box = QtWidgets.QGroupBox()
        self.render_settings_group_box.setStyleSheet(
            'QGroupBox {background-color: rgb(60, 60, 60); border-radius: 5px;}')
        self.main_right_v_box_layout.addWidget(self.render_settings_group_box)

        self.render_settings_form_layout = QtWidgets.QFormLayout()
        self.render_settings_form_layout.addRow('Start Frame: ', self.start_frame_spin_box)
        self.render_settings_form_layout.addRow('End Frame: ', self.end_frame_spin_box)
        self.render_settings_form_layout.addRow('Batch Size: ', self.allocation_spin_box)
        self.render_settings_form_layout.setContentsMargins(80, 4, 4, 4)
        self.render_settings_form_layout.setSpacing(4)
        self.render_settings_group_box.setLayout(self.render_settings_form_layout)

        self.main_right_v_box_layout.addWidget(self.advanced_settings_widget)
        self.main_right_v_box_layout.addWidget(self.render_push_button)
        self.main_right_v_box_layout.addWidget(self.restart_button)

    def create_connections(self) -> None:
        """Creates the connections."""
        self.render_push_button.clicked.connect(self.render_push_button_clicked)
        self.start_frame_spin_box.valueChanged.connect(self.start_frame_spin_box_value_changed)
        self.end_frame_spin_box.valueChanged.connect(self.end_frame_spin_box_value_changed)

        self.restart_button.clicked.connect(self.update_window)

    def create_call_backs(self) -> None:
        """Creates the call-backs."""
        om.MSceneMessage.addCallback(om.MSceneMessage.kAfterNew, self.update_window)
        om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, self.update_window)

    def create_script_jobs(self) -> None:
        """Creates the script jobs."""
        self.script_jobs.append(cmds.scriptJob(event=['DagObjectCreated', partial(self.update_window)]))

    def start_frame_spin_box_value_changed(self, value: int) -> None:
        """"""
        self.end_frame_spin_box.setMinimum(value)

        self.update_frame_range_spin_boxes_display()
        self.set_allocation_max_value()

    def end_frame_spin_box_value_changed(self, value: int) -> None:
        """"""
        self.start_frame_spin_box.setMaximum(value)

        self.update_frame_range_spin_boxes_display()
        self.set_allocation_max_value()

    def render_push_button_clicked(self):
        """Sets the Maya scene to Envy."""
        jobs_exported = 0
        use_tiled_rendering = self.advanced_settings_widget.use_tiled_rendering()

        for render_layer_widget in self.get_render_layers_items():  # FOR EACH LAYER
            if render_layer_widget.is_renderable():
                render_layer_name = render_layer_widget.get_render_layer_name()

                for camera_widget in render_layer_widget.get_camera_widgets():  # FOR EACH CAMERA
                    if camera_widget.is_renderable():
                        camera_name = camera_widget.get_camera_name()
                        divisions_x = self.advanced_settings_widget.get_divisions_x()
                        divisions_y = self.advanced_settings_widget.get_divisions_y()

                        if camera_widget.use_custom_frame_range():
                            start_frame = camera_widget.get_start_frame()
                            end_frame = camera_widget.get_end_frame()
                        elif render_layer_widget.use_custom_frame_range():
                            start_frame = render_layer_widget.get_start_frame()
                            end_frame = render_layer_widget.get_end_frame()
                        else:
                            start_frame = self.start_frame_spin_box.value()
                            end_frame = self.end_frame_spin_box.value()

                        if use_tiled_rendering is True:
                            image_output_prefix = self.advanced_settings_widget.get_image_output_prefix()
                            for i, min_max_pair in enumerate(self.compute_min_and_max_from_number_of_divisions(divisions_x, divisions_y)):
                                envy = maya_to_envy.MayaToEnvy()
                                envy.set_tiled_rendering_settings(
                                    min_bound=min_max_pair[0],
                                    max_bound=min_max_pair[1],
                                    image_output_prefix=image_output_prefix.replace('$RENDERLAYER', render_layer_name)
                                )
                                envy.set_start_frame(start_frame)
                                envy.set_end_frame(end_frame)
                                envy.set_allocation(self.allocation_spin_box.value())
                                envy.export_to_envy(camera_name, render_layer_name, i)
                                jobs_exported += 1
                        else:
                            envy = maya_to_envy.MayaToEnvy()
                            envy.set_start_frame(start_frame)
                            envy.set_end_frame(end_frame)
                            envy.set_allocation(self.allocation_spin_box.value())
                            envy.export_to_envy(camera_name, render_layer_name, 0)
                            jobs_exported += 1

        if not jobs_exported:
            om.MGlobal.displayWarning('[EnvyUI] No jobs exported.')

    @staticmethod
    def compute_min_and_max_from_number_of_divisions(divisions_x, divisions_y) -> list:
        resolution_x = cmds.getAttr('defaultResolution.width')
        resolution_y = cmds.getAttr('defaultResolution.height')
        increment_y = resolution_y // divisions_y
        increment_x = resolution_x // divisions_x
        min_max_pair_list = []
        for division_y in range(divisions_y):  # FOR EACH Y TILE
            y_min = increment_y * division_y
            y_max = increment_y * (division_y + 1)
            for division_x in range(divisions_x):  # FOR EACH X TILE
                x_min = increment_x * division_x
                x_max = increment_x * (division_x + 1)
                min_max_pair_list.append(((x_min, y_min), (x_max, y_max)))
        return min_max_pair_list

    def create_render_layers_widgets(self) -> None:
        """Creates the render_layers_widgets."""
        for render_layer in self.get_render_layers_items():
            render_layer.deleteLater()

        for render_layer in self.maya_to_envy.get_render_layers():
            render_layer_widget = render_layer_wdt.RenderLayerWidget()
            render_layer_widget.set_start_frame(self.start_frame_spin_box.value())
            render_layer_widget.set_end_frame(self.end_frame_spin_box.value())
            render_layer_widget.set_render_layer_name(render_layer)
            render_layer_widget.create_camera_widgets()
            render_layer_widget.set_renderable(cmds.getAttr(f'{render_layer}.renderable'))
            self.layer_renders_v_box_layout.addWidget(render_layer_widget)

    def get_render_layers_items(self) -> list:
        """Gets the render layers items."""
        render_layers = []

        for widget in self.layer_renders_group_box.children():
            if type(widget) is render_layer_wdt.RenderLayerWidget:
                render_layers.append(widget)

        return render_layers

    def set_allocation_max_value(self) -> None:
        """Sets the allocation max value."""
        self.allocation_spin_box.setMaximum(self.end_frame_spin_box.value() - self.start_frame_spin_box.value() + 1)

    def update_frame_range_spin_boxes_display(self) -> None:
        """Updates the frame range spin boxes display."""
        start_frame = self.start_frame_spin_box.value()
        end_frame = self.end_frame_spin_box.value()

        for render_layer in self.get_render_layers_items():
            if not render_layer.use_custom_frame_range():
                render_layer.set_start_frame(start_frame)
                render_layer.set_end_frame(end_frame)

            for camera in render_layer.get_camera_widgets():
                if not camera.use_custom_frame_range():
                    camera.set_start_frame(start_frame)
                    camera.set_end_frame(end_frame)

    def update_window(self) -> None:
        """Updates the window."""
        self.create_render_layers_widgets()
        self.start_frame_spin_box.setValue(cmds.getAttr('defaultRenderGlobals.startFrame'))
        self.end_frame_spin_box.setValue(cmds.getAttr('defaultRenderGlobals.endFrame'))

    def closeEvent(self, event):
        """Close event."""
        if isinstance(self, EnvyUI):
            super(EnvyUI, self).closeEvent(event)

            self.geometry = self.saveGeometry()

    def showEvent(self, event):
        """Show event."""
        super(EnvyUI, self).showEvent(event)

        if self.geometry:
            self.restoreGeometry(self.geometry)

        self.update_window()
