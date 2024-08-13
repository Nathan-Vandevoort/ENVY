import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om

try:
    import PySide2.QtWidgets as QtWidgets
    from shiboken2 import wrapInstance
except ModuleNotFoundError:
    import PySide6.QtWidgets as QtWidgets
    from shiboken6 import wrapInstance


class EnvyMenu:

    def __init__(self):
        maya_window_ptr = omui.MQtUtil.mainWindow()

        self.maya_window = wrapInstance(int(maya_window_ptr), QtWidgets.QWidget)
        self.maya_main_menu = self.maya_window.findChild(QtWidgets.QMenuBar)

    def add_envy_menu(self):
        if not self.maya_window.findChild(QtWidgets.QMenu, 'MainEnvyMenu'):
            envy_menu = QtWidgets.QMenu('Envy', self.maya_window)
            envy_menu.setObjectName('MainEnvyMenu')
            self.maya_main_menu.addMenu(envy_menu)

    def remove_envy_menu(self):
        envy_menu = self.maya_window.findChild(QtWidgets.QMenu, 'MainEnvyMenu')

        if envy_menu:
            self.maya_main_menu.removeAction(envy_menu.menuAction())
            envy_menu.deleteLater()
        else:
            om.MGlobal.displayWarning('Envy menu not found for removal.')


def maya_useNewAPI():
    """"""
    pass


def initializePlugin(plugin):
    """"""    
    vendor = "Envy"
    version = "1.0.0"

    plugin_fn = om.MFnPlugin(plugin, vendor, version)
    
    EnvyMenu().add_envy_menu()

    om.MGlobal.displayInfo('[Envy] Envy initialized.')


def uninitializePlugin(plugin):
    """"""
    EnvyMenu().remove_envy_menu()

    plugin_fn = om.MFnPlugin(plugin)

    om.MGlobal.displayInfo('[Envy] Envy uninitialized.')
