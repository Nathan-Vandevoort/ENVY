"""
========================================================================================================================
Name: frame_range_widget.py
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

import os


class FrameRangeWidget(QtWidgets.QWidget):

    def __init__(self):
        """"""
        super(FrameRangeWidget, self).__init__()

        self.icons_path = os.path.join(os.path.dirname(__file__), 'icons')

        self.edit_frame_range_push_button = None
        self.start_frame_spin_box = None
        self.end_frame_spin_box = None

        self.main_layout = None
        self.render_frame_range_group_box = None
        self.render_frame_range_h_box_layout = None

        self.setEnabled(False)

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_widgets(self) -> None:
        """Creates the widgets."""
        self.edit_frame_range_push_button = QtWidgets.QPushButton()
        self.edit_frame_range_push_button.setCheckable(True)
        self.edit_frame_range_push_button.setFixedSize(26, 26)
        self.edit_frame_range_push_button.setIcon(QtGui.QIcon(os.path.join(self.icons_path, 'clock-three.png')))
        self.edit_frame_range_push_button.setIconSize(QtCore.QSize(18, 18))
        self.edit_frame_range_push_button.setStyleSheet('''
                            QPushButton {
                                background-color: rgb(45, 45, 45); 
                                border-radius: 5px; 
                            }

                            QPushButton:checked {
                                background-color: rgb(54, 103, 124); 
                                border: none;
                            }''')

        self.start_frame_spin_box = QtWidgets.QSpinBox()
        self.start_frame_spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.start_frame_spin_box.setFixedSize(60, 20)
        self.start_frame_spin_box.setStyleSheet('''
            QSpinBox {
                background-color: rgb(40, 40, 40); 
                border-radius: 5px;
            }''')

        self.end_frame_spin_box = QtWidgets.QSpinBox()
        self.end_frame_spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.end_frame_spin_box.setFixedSize(60, 20)
        self.end_frame_spin_box.setMaximum(10000)
        self.end_frame_spin_box.setStyleSheet('''
                    QSpinBox {
                        background-color: rgb(40, 40, 40); 
                        border-radius: 5px;
                    }''')

    def create_layouts(self) -> None:
        """Creates the layouts."""
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.addWidget(self.edit_frame_range_push_button)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(2)

        self.render_frame_range_group_box = QtWidgets.QGroupBox()
        self.render_frame_range_group_box.setEnabled(False)
        self.render_frame_range_group_box.setFixedWidth(132)
        self.render_frame_range_group_box.setStyleSheet(
            'QGroupBox {background-color: rgb(60, 60, 60); border-radius: 5px;}')
        self.main_layout.addWidget(self.render_frame_range_group_box)

        self.render_frame_range_h_box_layout = QtWidgets.QHBoxLayout()
        self.render_frame_range_h_box_layout.addWidget(self.start_frame_spin_box)
        self.render_frame_range_h_box_layout.addWidget(self.end_frame_spin_box)
        self.render_frame_range_h_box_layout.setContentsMargins(2, 0, 0, 0)
        self.render_frame_range_h_box_layout.setSpacing(2)
        self.render_frame_range_group_box.setLayout(self.render_frame_range_h_box_layout)

    def create_connections(self) -> None:
        """Creates the connections."""
        self.edit_frame_range_push_button.toggled.connect(self.edit_frame_range_push_button_toggled)
        self.start_frame_spin_box.valueChanged.connect(self.start_frame_spin_box_value_changed)
        self.end_frame_spin_box.valueChanged.connect(self.end_frame_spin_box_value_changed)

    def edit_frame_range_push_button_toggled(self, checked: bool) -> None:
        """"""
        self.render_frame_range_group_box.setEnabled(checked)

    def start_frame_spin_box_value_changed(self, value: int) -> None:
        """"""
        self.end_frame_spin_box.setMinimum(value)

    def end_frame_spin_box_value_changed(self, value: int) -> None:
        """"""
        self.start_frame_spin_box.setMaximum(value)

    def get_start_frame(self) -> int:
        """Gets the start frame."""
        start_frame = self.start_frame_spin_box.value()

        return start_frame

    def get_end_frame(self) -> int:
        """Gets the end frame."""
        end_frame = self.end_frame_spin_box.value()

        return end_frame

    def set_start_frame(self, frame: int) -> None:
        """Sets the start frame."""
        self.start_frame_spin_box.setValue(frame)
        self.end_frame_spin_box.setMinimum(frame)

    def set_end_frame(self, frame: int) -> None:
        """SEts the end frame."""
        self.end_frame_spin_box.setValue(frame)
        self.start_frame_spin_box.setMaximum(frame)

    def use_custom_frame_range(self) -> bool:
        """"""
        custom_time = self.edit_frame_range_push_button.isChecked()

        return custom_time