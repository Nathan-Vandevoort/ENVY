"""
========================================================================================================================
Name: envy.py
========================================================================================================================
"""
try:
    import PySide2.QtWidgets as QtWidgets
    from shiboken2 import wrapInstance
except ModuleNotFoundError:
    import PySide6.QtWidgets as QtWidgets
    from shiboken6 import wrapInstance

import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om

import sys

new_path = 'Z:/Envy/__ENVYTEST__/Plugins/eMaya'
if new_path not in sys.path:
    sys.path.append(new_path)


envy_menu = None


def maya_main_window() -> any:
    """Gets the Maya main window widget as a Python object."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    main_window = wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

    return main_window


class EnvyMenu:

    def __init__(self):
        """"""
        maya_window_ptr = omui.MQtUtil.mainWindow()
        self.maya_window = wrapInstance(int(maya_window_ptr), QtWidgets.QWidget)
        self.maya_main_menu = self.maya_window.findChild(QtWidgets.QMenuBar)

        self.envy_ui = EnvyUI()

    def add_envy_menu(self):
        """Adds the Envy menu to the main Maya window."""
        if not self.maya_window.findChild(QtWidgets.QMenu, 'MainEnvyMenu'):
            main_envy_menu = QtWidgets.QMenu('Envy', self.maya_window)
            main_envy_menu.setObjectName('MainEnvyMenu')
            self.maya_main_menu.addMenu(main_envy_menu)

            export_to_envy = main_envy_menu.addAction('Export to Envy')
            export_to_envy.triggered.connect(self.show_envy_ui)

    def show_envy_ui(self):
        """Shows the Envy UI."""
        self.envy_ui.show()

    def remove_envy_menu(self):
        """Removes the Envy menu from the main Maya window."""
        main_envy_menu = self.maya_window.findChild(QtWidgets.QMenu, 'MainEnvyMenu')

        if main_envy_menu:
            self.maya_main_menu.removeAction(main_envy_menu.menuAction())
            main_envy_menu.deleteLater()
        else:
            om.MGlobal.displayWarning('Envy menu not found for removal.')


def maya_useNewAPI():
    """"""
    pass


def initializePlugin(plugin):
    """"""
    global envy_menu

    vendor = 'Mauricio Gonzalez Soto'
    version = '1.0.0'

    plugin_fn = om.MFnPlugin(plugin, vendor, version)

    envy_menu = EnvyMenu()
    envy_menu.add_envy_menu()

    om.MGlobal.displayInfo('[Envy] Envy initialized.')


def uninitializePlugin(plugin):
    """"""
    global envy_menu

    if envy_menu:
        envy_menu = EnvyMenu()
        envy_menu.remove_envy_menu()

        envy_menu = None

    plugin_fn = om.MFnPlugin(plugin)

    om.MGlobal.displayInfo('[Envy] Envy uninitialized.')
