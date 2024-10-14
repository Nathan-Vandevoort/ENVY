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

e_maya_ui_path = 'Z:/envy/plugins/eMaya/ui'

if e_maya_ui_path not in sys.path:
    sys.path.insert(0, e_maya_ui_path)

import envy_ui


def maya_main_window() -> any:
    """Gets the Maya main window widget as a Python object."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    main_window = wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

    return main_window


def add_envy_menu():
    """"""
    maya_window = maya_main_window()
    maya_main_menu = maya_window.findChild(QtWidgets.QMenuBar)

    if not maya_window.findChild(QtWidgets.QMenu, 'MainEnvyMenu'):
        main_envy_menu = QtWidgets.QMenu('Envy', maya_window)
        main_envy_menu.setObjectName('MainEnvyMenu')
        main_envy_menu.setTearOffEnabled(True)
        maya_main_menu.addMenu(main_envy_menu)

        export_to_envy = main_envy_menu.addAction('Export to Envy')
        export_to_envy.triggered.connect(show_envy_window)


def remove_envy_menu():
    """"""
    maya_window = maya_main_window()
    maya_main_menu = maya_window.findChild(QtWidgets.QMenuBar)
    main_envy_menu = maya_window.findChild(QtWidgets.QMenu, 'MainEnvyMenu')

    if main_envy_menu:
        maya_main_menu.removeAction(main_envy_menu.menuAction())
        main_envy_menu.deleteLater()
    else:
        om.MGlobal.displayWarning('Envy menu not found for removal.')


def show_envy_window():
    """"""
    envy_window = envy_ui.EnvyUI()
    envy_window.show_window()


def maya_useNewAPI():
    """"""
    pass


def initializePlugin(plugin):
    """"""
    vendor = 'Mauricio Gonzalez Soto'
    version = '1.0.0'

    plugin_fn = om.MFnPlugin(plugin, vendor, version)

    add_envy_menu()

    om.MGlobal.displayInfo('[Envy] Envy initialized.')


def uninitializePlugin(plugin):
    """"""
    remove_envy_menu()

    plugin_fn = om.MFnPlugin(plugin)

    om.MGlobal.displayInfo('[Envy] Envy uninitialized.')
