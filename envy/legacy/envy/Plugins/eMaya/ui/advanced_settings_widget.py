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

import imp
imp.reload(frame_range_wdt)
import collapsibleWidget

class AdvancedSettingsWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(AdvancedSettingsWidget, self).__init__(parent)

        self.layout = QtWidgets.QVBoxLayout()
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setMaximumHeight(600)

        self.collapsible_widget = collapsibleWidget.CollapsibleWidget()
        self.collapsible_widget.max_height = 200
        self.toggle_tiled_widget = QtWidgets.QCheckBox()
        self.toggle_tiled_widget.setText('Enable Tiled Rendering')

        self.num_tiles_x_widget = QtWidgets.QSpinBox()
        self.num_tiles_y_widget = QtWidgets.QSpinBox()
        self.image_output_prefix_widget = QtWidgets.QLineEdit('<Scene>/$RENDERLAYER/<Camera>_$TILEINDEX')

        self.toggle_tiled_organizer_widget = QtWidgets.QGroupBox()
        self.toggle_tiled_organizer_widget_layout = QtWidgets.QVBoxLayout()

        self.content_area_widget = QtWidgets.QGroupBox()
        self.content_area_layout = QtWidgets.QVBoxLayout()

        self.user_input_widget = QtWidgets.QGroupBox()
        self.user_input_widget.setEnabled(False)
        self.user_input_layout = QtWidgets.QFormLayout()

        self.toggle_tiled_widget.toggled.connect(self.toggle_use_tiled_rendering)

        self.create_widgets()
        self.create_layouts()
        self.setLayout(self.layout)

    def create_widgets(self) -> None:
        """Create the Widgets"""
        self.collapsible_widget.toggle_button.setStyleSheet('''
                            QToolButton {
                                background-color: rgb(40, 40, 40); 
                                border-radius: 5px;
                            }''')

        self.content_area_widget.setStyleSheet('''
            QGroupBox {background-color: rgb(60, 60, 60); 
            border-radius: 5px;}
            ''')

        self.num_tiles_x_widget.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.num_tiles_x_widget.setFixedSize(75, 20)
        self.num_tiles_x_widget.setMinimum(1)
        self.num_tiles_x_widget.setStyleSheet('''
                            QSpinBox {
                                background-color: rgb(40, 40, 40); 
                                border-radius: 5px;
                            }''')

        self.num_tiles_y_widget.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.num_tiles_y_widget.setFixedSize(75, 20)
        self.num_tiles_y_widget.setMinimum(1)
        self.num_tiles_y_widget.setStyleSheet('''
                                    QSpinBox {
                                        background-color: rgb(40, 40, 40); 
                                        border-radius: 5px;
                                    }''')

        self.image_output_prefix_widget.setFixedSize(300, 30)
        self.image_output_prefix_widget.setStyleSheet('''
                                    QLineEdit {
                                        background-color: rgb(40, 40, 40); 
                                        border-radius: 5px;
                                    }''')

        self.user_input_widget.setStyleSheet(
            '''
            QGroupBox {background-color: rgb(60, 60, 60); 
            border-radius: 5px;}
            '''
                                               )

    def toggle_use_tiled_rendering(self, checked: bool):
        self.user_input_widget.setEnabled(checked)

    def create_layouts(self):
        self.user_input_layout.addRow('Tiles X: ', self.num_tiles_x_widget)
        self.user_input_layout.addRow('Tiles Y: ', self.num_tiles_y_widget)
        self.user_input_layout.addRow('Image: ', self.image_output_prefix_widget)
        self.user_input_layout.setSpacing(4)
        self.user_input_widget.setLayout(self.user_input_layout)

        self.content_area_layout.addWidget(self.toggle_tiled_widget)
        self.content_area_layout.addWidget(self.user_input_widget)
        self.content_area_widget.setLayout(self.content_area_layout)

        self.collapsible_widget.add_widget(self.content_area_widget)
        self.layout.addWidget(self.collapsible_widget)

    def get_divisions_x(self):
        return int(self.num_tiles_x_widget.value())

    def get_divisions_y(self):
        return int(self.num_tiles_y_widget.value())

    def use_tiled_rendering(self):
        return self.toggle_tiled_widget.isChecked()

    def get_image_output_prefix(self):
        return self.image_output_prefix_widget.text()


if __name__ == '__main__':
    class MainWindow(QtWidgets.QMainWindow):
        def __init__(self, event_loop=None):
            super().__init__()
            self.event_loop = event_loop
            self.widget = AdvancedSettingsWidget()
            self.setCentralWidget(self.widget)

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())