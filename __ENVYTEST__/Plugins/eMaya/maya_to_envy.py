"""
========================================================================================================================
Name: maya_to_envy.py
========================================================================================================================
"""
import maya.api.OpenMaya as om
import maya.cmds as cmds

from pathlib import Path
import json
import os


class MayaToEnvy(object):
    ARNOLD = 'arnold'
    REDSHIFT = 'redshift'
    VRAY = 'vray'

    def __init__(self):
        """"""
        self.CLASS_NAME = __class__.__name__

        self.maya_file = None
        self.project_path = None
        self.maya_version = None
        self.render_engine = None
        self.cameras = []
        self.render_layers = []
        self.start_frame = 0
        self.end_frame = 0

    def check_file_nodes_paths(self) -> list:
        """Checks the file nodes paths."""
        file_nodes = cmds.ls(type='file')
        invalid_paths = []

        for file_node in file_nodes:
            file_texture_path = cmds.getAttr(file_node + '.fileTextureName')

            if not self.is_a_valid_file(file_texture_path):
                invalid_paths.append(file_texture_path)

        return invalid_paths

    def check_paths(self) -> bool:
        """Checks paths."""
        are_paths_valid = True

        paths = {
            'References': self.check_references_paths(),
            'File Nodes': self.check_file_nodes_paths()
        }

        for name, nodes_paths in paths.items():
            if nodes_paths:
                om.MGlobal.displayWarning(f'[{self.CLASS_NAME}] Missing {name}')

                for node_path in nodes_paths:
                    om.MGlobal.displayWarning(f'[{self.CLASS_NAME}] \t{node_path}')

                    are_paths_valid = False

        return are_paths_valid

    def check_references_paths(self) -> list:
        """Checks the references paths."""
        reference_nodes = cmds.ls(type='reference')
        invalid_paths = []

        for reference_node in reference_nodes:
            reference_path = cmds.referenceQuery(reference_node, filename=True)

            if not self.is_a_valid_file(reference_path):
                invalid_paths.append(reference_path)

        return invalid_paths

    def export_to_envy(self) -> None:
        """Exports to envy."""
        if not self.check_paths():
            om.MGlobal.displayError(f'[{self.CLASS_NAME}] Export to Envy failed. Paths not found.')
            return

        self.get_scene_information()

        if not self.maya_file:
            om.MGlobal.displayError(f'[{self.CLASS_NAME}] There is not Maya file saved.')
            return

        if self.render_engine == MayaToEnvy.ARNOLD:
            cmds.setAttr('defaultArnoldRenderOptions.log_verbosity', 2)
            cmds.setAttr('defaultArnoldRenderOptions.log_to_console', 1)

            om.MGlobal.displayInfo(f'[{self.CLASS_NAME}] defaultArnoldRenderOptions.log_verbosity = 2.')
            om.MGlobal.displayInfo(f'[{self.CLASS_NAME}] defaultArnoldRenderOptions.log_to_console = 1.')

            if not self.save_file():
                return

        elif self.render_engine == MayaToEnvy.REDSHIFT:
            cmds.setAttr('redshiftOptions.logLevel', 2)

            om.MGlobal.displayInfo(f'[{self.CLASS_NAME}] redshiftOptions.logLevel = 2.')

            if not self.save_file():
                return
        elif self.render_engine == MayaToEnvy.VRAY:
            cmds.setAttr('vraySettings.sys_message_level', 3)
            cmds.setAttr('vraySettings.sys_progress_increment', 1)

            om.MGlobal.displayInfo(f'[{self.CLASS_NAME}] vraySettings.sys_message_level = 3.')
            om.MGlobal.displayInfo(f'[{self.CLASS_NAME}] vraySettings.sys_progress_increment = 1.')

            if not self.save_file():
                return
        else:
            om.MGlobal.displayError(f'{[self.CLASS_NAME]} Render engine not supported.')
            return

        for frame in range(self.start_frame, self.end_frame + 1):
            for camera in self.cameras:
                for render_layer in self.render_layers:
                    maya_file_name = Path(self.maya_file).stem

                    json_path = os.path.join(
                        self.project_path,
                        'data',
                        f'{maya_file_name}_{camera}_{render_layer}_{str(frame).zfill(4)}_{str(frame).zfill(4)}.json')

                    settings = {
                        'maya_file': self.maya_file,
                        'project_path': self.project_path,
                        'maya_version': self.maya_version,
                        'render_engine': self.render_engine,
                        'camera': camera,
                        'render_layer': render_layer,
                        'start_frame': frame,
                        'end_frame': frame,
                        'maya_file_modification_time': os.path.getmtime(self.maya_file)}

                    with open(json_path, 'w') as file_to_write:
                        json.dump(settings, file_to_write, indent=4)

        om.MGlobal.displayInfo(f'[{self.CLASS_NAME}] Export to Envy was successfully.')

    @staticmethod
    def is_a_valid_file(file: str) -> bool:
        """Checks if is a valid file."""
        if file:
            if os.path.exists(file):
                return True
            elif file.startswith('Z:/'):
                return True

        return False

    def get_enabled_render_layers(self):
        """Gets the enabled render layers."""
        all_layers = cmds.ls(type='renderLayer', long=True)
        render_layers = []

        for layer in all_layers:
            if cmds.referenceQuery(layer, isNodeReferenced=True):
                is_referenced = cmds.referenceQuery(layer, isNodeReferenced=True)
            else:
                is_referenced = False

            if not is_referenced:
                render_layers.append(layer)

        enabled_layers = [layer for layer in render_layers if cmds.getAttr(f"{layer}.renderable")]

        self.render_layers = enabled_layers

    def get_scene_information(self) -> None:
        """Gets the scene information."""
        self.project_path = cmds.workspace(active=True, query=True)
        self.maya_file = cmds.file(query=True, sceneName=True)
        self.maya_version = cmds.about(query=True, version=True)
        self.render_engine = cmds.getAttr('defaultRenderGlobals.currentRenderer')

        self.cameras = [camera for camera in cmds.ls(cameras=True) if cmds.getAttr(f'{camera}.renderable')]
        self.start_frame = int(cmds.getAttr('defaultRenderGlobals.startFrame'))
        self.end_frame = int(cmds.getAttr('defaultRenderGlobals.endFrame'))

        self.get_enabled_render_layers()

    def save_file(self) -> bool:
        """Saves the file."""
        om.MGlobal.displayWarning(f'[{self.CLASS_NAME}] File must be saved.')

        result = cmds.confirmDialog(
            title='Export to Envy',
            message='File must be save it to export to Envy.\nDo you want to save it?',
            button=['Yes', 'No'],
            defaultButton='Yes',
            cancelButton='No',
            dismissString='No')

        if result == 'Yes':
            cmds.file(save=True)
            return True
        else:
            om.MGlobal.displayError(f'[{self.CLASS_NAME}] Failed exporting to Envy.')
            return False


if __name__ == '__main__':
    maya_to_envy = MayaToEnvy()
    maya_to_envy.export_to_envy()
