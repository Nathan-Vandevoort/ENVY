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
        """"""
        maya_window_ptr = omui.MQtUtil.mainWindow()
        self.maya_window = wrapInstance(int(maya_window_ptr), QtWidgets.QWidget)
        self.maya_main_menu = self.maya_window.findChild(QtWidgets.QMenuBar)

    def add_envy_menu(self):
        """Adds the Envy menu to the main Maya window."""
        if not self.maya_window.findChild(QtWidgets.QMenu, 'MainEnvyMenu'):
            envy_menu = QtWidgets.QMenu('Envy', self.maya_window)
            envy_menu.setObjectName('MainEnvyMenu')
            envy_menu.addAction('Export to Envy', self.export_to_envy)
            self.maya_main_menu.addMenu(envy_menu)

    def export_to_envy(self):
        """"""
        om.MGlobal.displayInfo('TODO: export_to_envy')

    def remove_envy_menu(self):
        """Removes the Envy menu from the main Maya window."""
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

    envy_menu = EnvyMenu()
    envy_menu.add_envy_menu()

    om.MGlobal.displayInfo('[Envy] Envy initialized.')


def uninitializePlugin(plugin):
    """"""
    envy_menu = EnvyMenu()
    envy_menu.remove_envy_menu()

    plugin_fn = om.MFnPlugin(plugin)

    om.MGlobal.displayInfo('[Envy] Envy uninitialized.')
