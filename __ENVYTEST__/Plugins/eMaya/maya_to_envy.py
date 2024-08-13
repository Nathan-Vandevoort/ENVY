"""
========================================================================================================================
Name: maya_to_envy.py
========================================================================================================================
"""
import maya.api.OpenMaya as om
import maya.cmds as cmds

import json
import os


class MayaToEnvy(object):

    def __init__(self):
        """"""
        self.CLASS_NAME = __class__.__name__

        self.maya_file = None
        self.project_path = None
        self.maya_version = None
        self.render_engine = None
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

        if self.render_engine == 'arnold':
            if cmds.getAttr('defaultArnoldRenderOptions.log_verbosity') != 2:
                cmds.setAttr('defaultArnoldRenderOptions.log_verbosity', 2)

                om.MGlobal.displayInfo(f'[{self.CLASS_NAME}] Log verbosity set to Info. File must be saved.')

                result = cmds.confirmDialog(
                    title='Export to Envy',
                    message='File must be save it to export to Envy.\nDo you want to save it?',
                    button=['Yes', 'No'],
                    defaultButton='Yes',
                    cancelButton='No',
                    dismissString='No')

                if result == 'Yes':
                    cmds.file(save=True)
                else:
                    om.MGlobal.displayError(f'[{self.CLASS_NAME}] Failed exporting to Envy.')

        json_path = os.path.join(self.project_path, 'data', 'test.json')
        settings = {
            'maya_file': self.maya_file,
            'project_path': self.project_path,
            'maya_version': self.maya_version,
            'render_engine': self.render_engine,
            'render_layers': self.render_layers,
            'start_frame': self.start_frame,
            'end_frame': self.end_frame,
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

        self.start_frame = cmds.getAttr('defaultRenderGlobals.startFrame')
        self.end_frame = cmds.getAttr('defaultRenderGlobals.endFrame')

        self.get_enabled_render_layers()


if __name__ == '__main__':
    maya_to_envy = MayaToEnvy()
    maya_to_envy.export_to_envy()
