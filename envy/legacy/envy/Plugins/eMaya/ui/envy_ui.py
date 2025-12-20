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

import webbrowser
import sys
import os
import re

e_maya_ui_path = os.path.dirname(__file__)
e_maya_path = os.path.dirname(e_maya_ui_path)

if e_maya_path not in sys.path:
    sys.path.append(e_maya_path)

if e_maya_ui_path not in sys.path:
    sys.path.append(e_maya_ui_path)

from render_layer_widget import RenderLayerWidget
import frame_layout
from spin_box import MSpinBox
import maya_to_envy

import imp
imp.reload(frame_layout)


def maya_main_window() -> any:
    """Gets the Maya main window widget as a Python object."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    main_window = wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

    return main_window


class EnvyUI(QtWidgets.QDialog):
    WINDOW_NAME = 'Envy'
    WINDOW_TITLE = 'EnvyUI'

    ARNOLD = 'arnold'
    REDSHIFT = 'redshift'
    V_RAY = 'vray'

    window_instance = None

    def __init__(self, parent=maya_main_window()):
        """"""
        super(EnvyUI, self).__init__(parent)
        self.geometry = None

        self.maya_to_envy = maya_to_envy.MayaToEnvy()

        self.file_name_prefix_line_edit = None
        self.start_frame_spin_box = None
        self.end_frame_spin_box = None
        self.batch_size_spin_box = None
        self.auto_save_file_check_box = None
        self.increment_and_save_check_box = None
        self.use_tiled_rendering_check_box = None
        self.tiles_x_spin_box = None
        self.tiles_y_spin_box = None
        self.export_to_envy_push_button = None

        self.layer_renders_v_box_layout = None
        self.layer_renders_group_box = None

        self.script_jobs = []

        # QDialog settings.
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(50, 50, 50))

        self.setAutoFillBackground(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(300)
        self.setModal(True)
        self.setObjectName(self.WINDOW_TITLE)
        self.setPalette(palette)
        self.setWindowTitle(self.WINDOW_NAME)

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.setSpacing(2)

        self.create_menu_bar()
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

    def create_menu_bar(self):
        """Creates the menu bar."""
        # Main QMenuBar.
        main_menu_bar = QtWidgets.QMenuBar()
        self.main_layout.setMenuBar(main_menu_bar)

        # Edit menu.
        edit_menu = main_menu_bar.addMenu('Edit')
        edit_menu.addAction('Reload', self.update_window)

        # Help menu.
        help_menu = main_menu_bar.addMenu('Help')
        help_menu.addAction('Help on Envy', self.show_help)

    def create_widgets(self) -> None:
        """Creates the widgets."""
        # File name prefix QLineEdit.
        self.file_name_prefix_line_edit = QtWidgets.QLineEdit()
        self.file_name_prefix_line_edit.setReadOnly(True)
        self.file_name_prefix_line_edit.setStyleSheet('''
            QLineEdit {
                background-color: rgb(40, 40, 40); 
                border-radius: 5px;
            }''')

        # Start frame MSpinBox.
        self.start_frame_spin_box = MSpinBox()
        self.start_frame_spin_box.setMaximum(10000)

        # End frame MSpinBox.
        self.end_frame_spin_box = MSpinBox()
        self.end_frame_spin_box.setMaximum(10000)

        # Batch size MSpinBox.
        self.batch_size_spin_box = MSpinBox()
        self.batch_size_spin_box.setMinimum(1)

        # Auto sava file QCheckBox.
        self.auto_save_file_check_box = QtWidgets.QCheckBox('Auto Save File')
        self.auto_save_file_check_box.setChecked(True)

        # Increment and save QCheckBox.
        self.increment_and_save_check_box = QtWidgets.QCheckBox('Increment and Save')
        self.increment_and_save_check_box.setChecked(True)

        # Use tiled rendering QCheckBox.
        self.use_tiled_rendering_check_box = QtWidgets.QCheckBox('Use Tiled Rendering')

        # Tiles X MSpinBox.
        self.tiles_x_spin_box = MSpinBox()
        self.tiles_x_spin_box.setEnabled(False)
        self.tiles_x_spin_box.setRange(1, 100)

        # Tiles Y MSpinBox.
        self.tiles_y_spin_box = MSpinBox()
        self.tiles_y_spin_box.setEnabled(False)
        self.tiles_y_spin_box.setRange(1, 100)

        # Export to Envy QPushButton.
        self.export_to_envy_push_button = QtWidgets.QPushButton('Export To Envy')
        self.export_to_envy_push_button.setFixedHeight(30)
        self.export_to_envy_push_button.setStyleSheet('''
        QPushButton {
            background-color: rgb(30, 30, 30); 
            border-radius: 5px;}
            
        QPushButton:pressed {
            background-color: rgb(50, 50, 50);
            border: none;}''')

    def create_layouts(self) -> None:
        """Creates the layouts."""
        # Main left QVBoxLayout.
        main_left_v_box_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addLayout(main_left_v_box_layout)

        # Layer renders QGroupBox.
        self.layer_renders_group_box = QtWidgets.QGroupBox()
        self.layer_renders_group_box.setStyleSheet('''
        QGroupBox {
            background-color: rgb(30, 30, 30); 
            border-radius: 5px;}''')
        main_left_v_box_layout.addWidget(self.layer_renders_group_box)

        # Layer renders QVBoxLayout.
        self.layer_renders_v_box_layout = QtWidgets.QVBoxLayout()
        self.layer_renders_v_box_layout.setAlignment(QtCore.Qt.AlignTop)
        self.layer_renders_v_box_layout.setContentsMargins(4, 4, 4, 4)
        self.layer_renders_v_box_layout.setSpacing(2)
        self.layer_renders_group_box.setLayout(self.layer_renders_v_box_layout)

        # Main right QVBoxLayout.
        main_right_v_box_layout = QtWidgets.QVBoxLayout()
        main_right_v_box_layout.setAlignment(QtCore.Qt.AlignTop)
        main_right_v_box_layout.setSpacing(2)
        self.main_layout.addLayout(main_right_v_box_layout)

        # Render settings QGroupBox.
        render_settings_group_box = QtWidgets.QGroupBox()
        render_settings_group_box.setStyleSheet(
            'QGroupBox {background-color: rgb(60, 60, 60); border-radius: 5px;}')
        main_right_v_box_layout.addWidget(render_settings_group_box)

        # Render settings QFormLayout.
        render_settings_form_layout = QtWidgets.QFormLayout()
        render_settings_form_layout.addRow('File Name Prefix: ', self.file_name_prefix_line_edit)
        render_settings_form_layout.addRow('Start Frame: ', self.start_frame_spin_box)
        render_settings_form_layout.addRow('End Frame: ', self.end_frame_spin_box)
        render_settings_form_layout.addRow('Batch Size: ', self.batch_size_spin_box)
        render_settings_form_layout.setContentsMargins(30, 4, 4, 4)
        render_settings_form_layout.setSpacing(4)
        render_settings_group_box.setLayout(render_settings_form_layout)

        # Main right QWidget.
        main_right_widget = QtWidgets.QWidget()
        main_right_widget.setFixedHeight(20)
        main_right_v_box_layout.addWidget(main_right_widget)

        # Advanced settings main QVBoxLayout.
        advanced_settings_main_v_box_layout = QtWidgets.QVBoxLayout()
        advanced_settings_main_v_box_layout.setContentsMargins(0, 0, 0, 0)
        main_right_widget.setLayout(advanced_settings_main_v_box_layout)

        # Advanced settings MFrameLayout.
        advanced_settings_frame_layout = frame_layout.MFrameLayout('Advanced Settings', main_right_widget)
        advanced_settings_frame_layout.set_height(120)
        advanced_settings_main_v_box_layout.addWidget(advanced_settings_frame_layout)

        # Save file QGroupBox.
        save_file_group_box = QtWidgets.QGroupBox()
        save_file_group_box.setStyleSheet(
            'QGroupBox {background-color: rgb(60, 60, 60); border-radius: 5px;}')
        advanced_settings_frame_layout.add_widget(save_file_group_box)

        # Save file QFormLayout.
        save_file_form_layout = QtWidgets.QFormLayout()
        save_file_form_layout.addWidget(self.auto_save_file_check_box)
        save_file_form_layout.addWidget(self.increment_and_save_check_box)
        save_file_form_layout.setContentsMargins(112, 4, 4, 4)
        save_file_form_layout.setSpacing(4)
        save_file_group_box.setLayout(save_file_form_layout)

        # Tiled rendering QGroupBox.
        tiled_rendering_group_box = QtWidgets.QGroupBox()
        tiled_rendering_group_box.setStyleSheet(
            'QGroupBox {background-color: rgb(60, 60, 60); border-radius: 5px;}')
        advanced_settings_frame_layout.add_widget(tiled_rendering_group_box)

        # Tiled rendering QFormLayout.
        tiled_rendering_form_layout = QtWidgets.QFormLayout()
        tiled_rendering_form_layout.addWidget(self.use_tiled_rendering_check_box)
        tiled_rendering_form_layout.addRow('Tile X: ', self.tiles_x_spin_box)
        tiled_rendering_form_layout.addRow('Tile Y: ', self.tiles_y_spin_box)
        tiled_rendering_form_layout.setContentsMargins(80, 4, 4, 4)
        tiled_rendering_form_layout.setSpacing(4)
        tiled_rendering_group_box.setLayout(tiled_rendering_form_layout)

        main_right_v_box_layout.addStretch()
        main_right_v_box_layout.addWidget(self.export_to_envy_push_button)

    def create_connections(self) -> None:
        """Creates the connections."""
        self.start_frame_spin_box.valueChanged.connect(self.start_frame_spin_box_value_changed)
        self.end_frame_spin_box.valueChanged.connect(self.end_frame_spin_box_value_changed)

        self.auto_save_file_check_box.toggled.connect(self.auto_save_file_toggled_check_box)
        self.use_tiled_rendering_check_box.toggled.connect(self.use_tiled_rendering_toggled_check_box)
        self.export_to_envy_push_button.clicked.connect(self.export_to_envy_push_button_clicked)

    @staticmethod
    def show_help():
        """"""
        webbrowser.open('https://github.com/Nathan-Vandevoort/ENVY')

    def start_frame_spin_box_value_changed(self) -> None:
        """"""
        self.update_frame_range_spin_boxes_values()

    def end_frame_spin_box_value_changed(self) -> None:
        """"""
        self.update_frame_range_spin_boxes_values()

    def auto_save_file_toggled_check_box(self, checked: bool) -> None:
        """"""
        self.increment_and_save_check_box.setEnabled(checked)

    def use_tiled_rendering_toggled_check_box(self, checked: bool) -> None:
        """"""
        self.tiles_x_spin_box.setEnabled(checked)
        self.tiles_y_spin_box.setEnabled(checked)

    def export_to_envy_push_button_clicked(self):
        """Sets the Maya scene to Envy."""
        jobs_exported = 0
        use_tiled_rendering = self.use_tiled_rendering_check_box.isChecked()
        auto_save_file = self.auto_save_file_check_box.isChecked()

        for render_layer_widget in self.get_render_layers_items():  # FOR EACH LAYER
            if render_layer_widget.is_renderable():
                render_layer_name = render_layer_widget.get_render_layer_name()

                for camera_widget in render_layer_widget.get_camera_widgets():  # FOR EACH CAMERA
                    if camera_widget.is_renderable():
                        camera_name = camera_widget.get_camera_name()

                        if camera_widget.use_custom_frame_range():
                            start_frame = camera_widget.get_start_frame()
                            end_frame = camera_widget.get_end_frame()
                        elif render_layer_widget.use_custom_frame_range():
                            start_frame = render_layer_widget.get_start_frame()
                            end_frame = render_layer_widget.get_end_frame()
                        else:
                            start_frame = self.start_frame_spin_box.value()
                            end_frame = self.end_frame_spin_box.value()

                        if end_frame < start_frame:
                            message = f'Invalid frame range. Start frame: {start_frame} End frame: {end_frame}'

                            om.MGlobal.displayError(message)

                            message_box = QtWidgets.QMessageBox()
                            message_box.setIcon(QtWidgets.QMessageBox.Critical)
                            message_box.setText(message)
                            message_box.setWindowTitle('Envy')
                            message_box.exec_()

                            return

                        if use_tiled_rendering:
                            image_output_prefix = self.file_name_prefix_line_edit.text()

                            if not image_output_prefix:
                                message = 'There is no file name prefix set.'

                                om.MGlobal.displayError(message)

                                message_box = QtWidgets.QMessageBox()
                                message_box.setIcon(QtWidgets.QMessageBox.Critical)
                                message_box.setText(message)
                                message_box.setWindowTitle('Envy')
                                message_box.exec_()

                                return

                            image_output_prefix = f'{image_output_prefix}_$TILEINDEX'
                            divisions_x = self.tiles_x_spin_box.value()
                            divisions_y = self.tiles_y_spin_box.value()
                            divisions = self.compute_min_and_max_from_number_of_divisions(divisions_x, divisions_y)

                            for i, min_max_pair in enumerate(divisions):
                                envy = maya_to_envy.MayaToEnvy()
                                envy.set_auto_save_maya_file(auto_save_file)
                                envy.set_tiled_rendering_settings(
                                    min_bound=min_max_pair[0],
                                    max_bound=min_max_pair[1],
                                    image_output_prefix=image_output_prefix)
                                envy.set_start_frame(start_frame)
                                envy.set_end_frame(end_frame)
                                envy.set_allocation(self.batch_size_spin_box.value())
                                envy.export_to_envy(camera_name, render_layer_name, i)

                                jobs_exported += 1
                        else:
                            envy = maya_to_envy.MayaToEnvy()
                            envy.set_auto_save_maya_file(auto_save_file)
                            envy.set_start_frame(start_frame)
                            envy.set_end_frame(end_frame)
                            envy.set_allocation(self.batch_size_spin_box.value())
                            envy.export_to_envy(camera_name, render_layer_name, 0)

                            jobs_exported += 1

        if not jobs_exported:
            message = 'No jobs exported.'

            om.MGlobal.displayError(message)

            message_box = QtWidgets.QMessageBox()
            message_box.setIcon(QtWidgets.QMessageBox.Critical)
            message_box.setText(message)
            message_box.setWindowTitle('Envy')
            message_box.exec_()
        else:
            if auto_save_file:
                if self.increment_and_save_check_box.isChecked():
                    maya_file = cmds.file(query=True, sceneName=True)
                    base_name, ext = os.path.splitext(maya_file)
                    match = re.search(r'(\d+)(?!.*\d)', base_name)

                    if match:
                        num = match.group(1)
                        new_num = str(int(num) + 1).zfill(len(num))
                        new_base_name = base_name[:match.start()] + new_num
                        new_maya_file = new_base_name + ext
                    else:
                        new_maya_file = f'{base_name}.0001{ext}'

                    cmds.file(rename=new_maya_file)
                    cmds.file(save=True)

                    om.MGlobal.displayInfo(f'File saved as {new_maya_file}.')
                else:
                    if cmds.file(query=True, modified=True):
                        cmds.file(save=True)

                        om.MGlobal.displayInfo('File saved.')

    @staticmethod
    def compute_min_and_max_from_number_of_divisions(divisions_x, divisions_y) -> list:
        resolution_x = cmds.getAttr('defaultResolution.width')
        resolution_y = cmds.getAttr('defaultResolution.height')

        increment_y = resolution_y // divisions_y
        increment_x = resolution_x // divisions_x

        min_max_pair_list = []

        for division_y in range(divisions_y):
            y_min = increment_y * division_y
            y_max = increment_y * (division_y + 1)

            for division_x in range(divisions_x):
                x_min = increment_x * division_x
                x_max = increment_x * (division_x + 1)

                min_max_pair_list.append(((x_min, y_min), (x_max - 1, y_max - 1)))

        return min_max_pair_list

    def create_render_layers_widgets(self) -> None:
        """Creates the render_layers_widgets."""
        for render_layer in self.get_render_layers_items():
            render_layer.deleteLater()

        for render_layer in self.maya_to_envy.get_render_layers():
            render_layer_widget = RenderLayerWidget()
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
            if type(widget) is RenderLayerWidget:
                render_layers.append(widget)

        return render_layers

    def update_frame_range_spin_boxes_values(self) -> None:
        """Updates the frame range spin boxes values."""
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

        current_render_engine = cmds.getAttr('defaultRenderGlobals.currentRenderer')

        if current_render_engine == EnvyUI.ARNOLD:
            window_title = 'Envy - Arnold'
        elif current_render_engine == EnvyUI.REDSHIFT:
            window_title = 'Envy - Redshift'
        elif current_render_engine == EnvyUI.V_RAY:
            window_title = 'Envy - V-Ray'
        else:
            window_title = f'Envy - {current_render_engine} (No Supported)'

        self.setWindowTitle(window_title)

        if current_render_engine == EnvyUI.V_RAY:
            file_name_prefix = cmds.getAttr('vraySettings.fileNamePrefix')
        else:
            file_name_prefix = cmds.getAttr('defaultRenderGlobals.imageFilePrefix')

        self.file_name_prefix_line_edit.setText(file_name_prefix)

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
