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

    def __init__(self, parent=maya_main_window()):
        """"""
        super(EnvyUI, self).__init__(parent)
        self.maya_to_envy = maya_to_envy.MayaToEnvy()

        self.start_frame_spin_box = None
        self.end_frame_spin_box = None
        self.allocation_spin_box = None
        self.render_push_button = None

        self.main_layout = None
        self.main_left_v_box_layout = None
        self.layer_renders_group_box = None
        self.layer_renders_v_box_layout = None
        self.main_right_v_box_layout = None
        self.render_settings_group_box = None
        self.render_settings_form_layout = None

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
        self.create_render_layers_widgets()

    def create_widgets(self) -> None:
        """Creates the widgets."""
        self.start_frame_spin_box = QtWidgets.QSpinBox()
        self.start_frame_spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.start_frame_spin_box.setFixedWidth(75)
        self.start_frame_spin_box.setValue(cmds.getAttr('defaultRenderGlobals.startFrame'))

        self.end_frame_spin_box = QtWidgets.QSpinBox()
        self.end_frame_spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.end_frame_spin_box.setFixedWidth(75)
        self.end_frame_spin_box.setMaximum(10000)
        self.end_frame_spin_box.setValue(cmds.getAttr('defaultRenderGlobals.endFrame'))

        self.allocation_spin_box = QtWidgets.QSpinBox()
        self.allocation_spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.allocation_spin_box.setFixedWidth(75)
        self.allocation_spin_box.setMaximum(self.end_frame_spin_box.value() - self.start_frame_spin_box.value())
        self.allocation_spin_box.setMinimum(1)

        self.render_push_button = QtWidgets.QPushButton('Render')

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
            'QGroupBox {background-color: rgb(65, 65, 65); border-radius: 5px;}')
        self.main_right_v_box_layout.addWidget(self.render_settings_group_box)

        self.render_settings_form_layout = QtWidgets.QFormLayout()
        self.render_settings_form_layout.addRow('Start Frame: ', self.start_frame_spin_box)
        self.render_settings_form_layout.addRow('End Frame: ', self.end_frame_spin_box)
        self.render_settings_form_layout.addRow('Allocation: ', self.allocation_spin_box)
        self.render_settings_form_layout.setContentsMargins(80, 4, 4, 4)
        self.render_settings_form_layout.setSpacing(4)
        self.render_settings_group_box.setLayout(self.render_settings_form_layout)

        self.main_right_v_box_layout.addStretch()
        self.main_right_v_box_layout.addWidget(self.render_push_button)

    def create_connections(self) -> None:
        """Creates the connections."""
        self.render_push_button.clicked.connect(self.render_push_button_clicked)
        self.start_frame_spin_box.valueChanged.connect(self.start_frame_spin_box_value_changed)
        self.end_frame_spin_box.valueChanged.connect(self.end_frame_spin_box_value_changed)

    def start_frame_spin_box_value_changed(self, value: int) -> None:
        """"""
        self.end_frame_spin_box.setMinimum(value)
        self.set_allocation_max_value()

    def end_frame_spin_box_value_changed(self, value: int) -> None:
        """"""
        self.start_frame_spin_box.setMaximum(value)
        self.set_allocation_max_value()

    def render_push_button_clicked(self):
        """Sets the Maya scene to Envy."""
        jobs_exported = 0

        for render_layer_widget in self.get_render_layers_items():
            if render_layer_widget.is_renderable():
                render_layer_name = render_layer_widget.get_render_layer_name()

                for camera_widget in render_layer_widget.get_camera_widgets():
                    if camera_widget.is_renderable():
                        camera_name = camera_widget.get_camera_name()

                        envy = maya_to_envy.MayaToEnvy()
                        envy.set_allocation(self.allocation_spin_box.value())

                        if camera_widget.use_custom_frame_range():
                            envy.set_start_frame(camera_widget.get_start_frame())
                            envy.set_end_frame(camera_widget.get_end_frame())
                        elif render_layer_widget.use_custom_frame_range():
                            envy.set_start_frame(render_layer_widget.get_start_frame())
                            envy.set_end_frame(render_layer_widget.get_end_frame())

                        envy.export_to_envy(camera_name, render_layer_name)

                        jobs_exported += 1

        if not jobs_exported:
            om.MGlobal.displayWarning('[EnvyUI] No jobs exported.')

    def create_render_layers_widgets(self) -> None:
        """Creates the render_layers_widgets."""
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


try:
    ui.close()
    ui.deleteLater()
except:
    pass

ui = EnvyUI()
ui.show()
