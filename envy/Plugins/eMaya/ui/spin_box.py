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
except ModuleNotFoundError:
    import PySide2.QtWidgets as QtWidgets
    import PySide2.QtCore as QtCore
    import PySide2.QtGui as QtGui


class MSpinBox(QtWidgets.QSpinBox):

    def __init__(self, *args):
        """"""
        super(MSpinBox, self).__init__(*args)

        self.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.setFixedSize(75, 20)
        self.setStyleSheet('''
            QSpinBox {
                background-color: rgb(40, 40, 40); 
                border-radius: 5px;
            }''')

    def contextMenuEvent(self, event):
        """Context menu event."""
        event.ignore()
