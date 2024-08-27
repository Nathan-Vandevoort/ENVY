"""
========================================================================================================================
Name: maya_to_envy.py
========================================================================================================================
"""
import maya.api.OpenMaya as om
import maya.cmds as cmds

from pathlib import Path
import sys
import os


envy_path = 'Z:/Envy/'

if envy_path not in sys.path:
    sys.path.append(envy_path)


import envyJobs.job as job
from envyJobs.enums import Purpose as p


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

    def export_to_envy(self, camera: str, render_layer: str) -> None:
        """Exports to envy."""
        # if not self.check_paths():
        #     om.MGlobal.displayError(f'[{self.CLASS_NAME}] Export to Envy failed. Paths not found.')
        #     return
        if not self.get_maya_file():
            om.MGlobal.displayError(f'[{self.CLASS_NAME}] There is not Maya file saved.')
            return
        elif not cmds.objExists(camera):
            om.MGlobal.displayError(f'[{self.CLASS_NAME}] Camera does not exists.')
            return
        elif not cmds.objExists(render_layer):
            om.MGlobal.displayError(f'[{self.CLASS_NAME}] Render layer does not exists.')
            return

        self.render_engine = self.get_render_engine()

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

        maya_file_name = Path(self.get_maya_file()).stem
        camera_short_name = cmds.ls(camera, shortNames=True)[0]
        render_layer_short_name = render_layer.replace(':', '')

        render_job = job.Job(f'{maya_file_name}_{camera_short_name}_{render_layer_short_name}')
        render_job.add_range(self.get_start_frame(), self.get_end_frame(), 1)
        render_job.set_meta()
        render_job.set_allocation(3)
        render_job.set_purpose(p.RENDER)
        render_job.set_type('PLUGIN_eMaya')
        render_job.set_environment({
            'maya_file': self.get_maya_file(),
            'project_path': self.get_project_path(),
            'maya_version': self.get_maya_version(),
            'render_engine': self.get_render_engine(),
            'camera': camera,
            'render_layer': render_layer
        })
        render_job.write()

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

    @staticmethod
    def get_cameras() -> list:
        """Gets cameras."""
        return cmds.ls(cameras=True, long=True)

    @staticmethod
    def get_end_frame() -> int:
        """Gets the render end frame."""
        end_frame = cmds.getAttr('defaultRenderGlobals.endFrame')

        return int(end_frame)

    @staticmethod
    def get_maya_file() -> str:
        """Gets the Maya file."""
        return cmds.file(query=True, sceneName=True)

    @staticmethod
    def get_maya_version() -> str:
        """Gets the Maya version."""
        return cmds.about(query=True, version=True)

    @staticmethod
    def get_project_path() -> str:
        """Gets the project path."""
        return cmds.workspace(active=True, query=True)

    @staticmethod
    def get_render_engine() -> str:
        """Gets the current render engine."""
        return cmds.getAttr('defaultRenderGlobals.currentRenderer')

    def get_render_layers(self) -> list:
        """Gets the enabled render layers."""
        all_render_layers_layers = cmds.ls(type='renderLayer', long=True)
        render_layers = []

        for render_layer in all_render_layers_layers:
            if cmds.referenceQuery(render_layer, isNodeReferenced=True):
                is_referenced = cmds.referenceQuery(render_layer, isNodeReferenced=True)
            else:
                is_referenced = False

            if not is_referenced:
                if render_layer == 'defaultRenderLayer':
                    render_layers.append(render_layer)
                elif render_layer.startswith('rs_'):
                    render_layers.append(render_layer)
                else:
                    om.MGlobal.displayWarning(f'[{self.CLASS_NAME}] Render layer {render_layer} skipped.')

        return render_layers

    @staticmethod
    def get_start_frame() -> int:
        """Gets the render start frame."""
        start_frame = cmds.getAttr('defaultRenderGlobals.startFrame')

        return int(start_frame)

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
