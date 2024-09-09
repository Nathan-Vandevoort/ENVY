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
import re


envy_path = 'Z:/envy/'
utils_path = os.path.join(envy_path, 'utils')

if envy_path not in sys.path:
    sys.path.insert(0, envy_path)

if utils_path not in sys.path:
    sys.path.insert(0, utils_path)

import config_bridge as config

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
        self.allocation = 1

        self.tiled_rendering = False
        self.tile_bound_min = (0, 0)
        self.tile_bound_max = (100, 100)
        self.image_output_prefix = '<Scene>/<RenderLayer>/<Camera>_000'

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
            # 'References': self.check_references_paths(),
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

    def export_to_envy(self, camera: str, render_layer: str, tile_idx: int) -> None:
        """Exports to envy."""
        if not self.check_paths():
            om.MGlobal.displayError(f'[{self.CLASS_NAME}] Export to Envy failed. Paths not found.')
            return
        elif not self.is_maya_file_valid(self.get_maya_file()):
            return
        elif not self.is_project_path_valid(self.get_project_path()):
            return
        elif not cmds.objExists(camera):
            om.MGlobal.displayError(f'[{self.CLASS_NAME}] Camera does not exists.')
            return
        elif not cmds.objExists(render_layer):
            om.MGlobal.displayError(f'[{self.CLASS_NAME}] Render layer does not exists.')
            return

        self.render_engine = self.get_render_engine()

        # Each render engine method will return True if the Maya file needs to be saved.
        # If the user does not allow to save the Maya file, exporting to Envy will be aborted.

        if self.render_engine == MayaToEnvy.ARNOLD:
            if self.set_arnold_settings():
                if not self.save_file():
                    return
        elif self.render_engine == MayaToEnvy.REDSHIFT:
            if self.set_redshift_settings():
                if not self.save_file():
                    return
        elif self.render_engine == MayaToEnvy.VRAY:
            if self.set_vray_settings():
                if not self.save_file():
                    return
        else:
            om.MGlobal.displayError(f'{[self.CLASS_NAME]} Render engine {self.render_engine} not supported.')
            return

        from envyRepo.envyJobs.enums import Purpose
        import envyRepo.envyJobs.job as job

        maya_file_name = Path(self.get_maya_file()).stem
        camera_short_name = cmds.ls(camera, shortNames=True)[0].replace(':', '')
        render_layer_short_name = render_layer.replace(':', '')

        render_job = job.Job(f'{maya_file_name}_{camera_short_name}_{render_layer_short_name}_{str(tile_idx).zfill(3)}')
        render_job.add_range(self.start_frame, self.end_frame, 1)
        render_job.set_meta()
        render_job.set_allocation(self.allocation)
        render_job.set_purpose(Purpose.RENDER)
        render_job.set_type('PLUGIN_eMaya')

        environment = {
            'maya_file': self.get_maya_file(),
            'project_path': self.get_project_path(),
            'maya_version': self.get_maya_version(),
            'render_engine': self.get_render_engine(),
            'render_layer': render_layer,
            'camera': camera,
            'use_tiled_rendering': False
        }

        if self.tiled_rendering is True:
            environment['use_tiled_rendering'] = True
            environment['tile_bound_min'] = self.tile_bound_min
            environment['tile_bound_max'] = self.tile_bound_max
            environment['image_output_prefix'] = self.image_output_prefix.replace('$TILEINDEX', str(tile_idx).zfill(3))

        render_job.set_environment(environment)
        render_job.write()

        om.MGlobal.displayInfo(f'[{self.CLASS_NAME}] Exporting to Envy...\n'
                               f'\tmaya_file: {self.get_maya_file()}\n'
                               f'\tproject_path: {self.get_project_path()}\n'
                               f'\trender_engine: {self.get_render_engine()}\n'
                               f'\trender_layer: {render_layer}\n'
                               f'\tcamera: {camera}\n'
                               f'\tstart_frame: {self.start_frame}\n'
                               f'\tend_frame: {self.end_frame}\n'
                               f'\tallocation: {self.allocation}\n')

        om.MGlobal.displayInfo(f'[{self.CLASS_NAME}] Exported job to envy.')

    @staticmethod
    def is_a_valid_file(file: str) -> bool:
        """Checks if is a valid file."""
        if file:
            if os.path.exists(file):
                return True
            elif not re.match("^[a-yA-Y]]*", file):
                return True

        return False

    def is_maya_file_valid(self, maya_file: str) -> bool:
        """Checks if the maya file exists."""
        print(maya_file)
        if not maya_file:
            om.MGlobal.displayError(f'[{self.CLASS_NAME}] There is not Maya file saved.')
            return False
        elif re.match("^[a-yA-Y]]*", maya_file):
            om.MGlobal.displayError(f'[{self.CLASS_NAME}] Maya file must be on a server (//titansrv, Z:/, //veloxsrv)')
            return False
        elif not os.path.exists(maya_file):
            om.MGlobal.displayError(f'[{self.CLASS_NAME}] Maya file does not exist.')
        else:
            return True

    def is_project_path_valid(self, project_path: str) -> bool:
        """Checks if the project exists."""
        print(project_path)
        if re.match("^[a-yA-Y]]*", project_path):
            om.MGlobal.displayError(f'[{self.CLASS_NAME}] Project must be on a server (//titansrv, Z:/, //veloxsrv)')
            return False
        elif not os.path.exists(project_path):
            om.MGlobal.displayError(f'[{self.CLASS_NAME}] Project path does not exist.')
            return False
        else:
            return True

    def get_end_frame(self) -> int:
        """Gets the render end frame."""
        return self.end_frame

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

    def get_cameras_from_render_layer(self, render_layer: str) -> list:
        """Gets the cameras in the current render layer."""
        if not cmds.objExists(render_layer):
            om.MGlobal.displayError(f'[{self.CLASS_NAME}] Render layer {render_layer} does not exists.')
            return []
        elif not cmds.objectType(render_layer, isType='renderLayer'):
            om.MGlobal.displayError(f'[{self.CLASS_NAME}] {render_layer} is not a render layer.')
            return []

        render_layer_members = cmds.editRenderLayerMembers(render_layer, query=True, fullNames=True)
        cameras = set()

        if render_layer_members:
            for obj in render_layer_members:
                children_shapes = cmds.listRelatives(obj, children=True, shapes=True, fullPath=True)

                if children_shapes:
                    for shape in children_shapes:
                        if cmds.objectType(shape, isType='camera'):
                            if not cmds.getAttr(f'{shape}.orthographic'):
                                cameras.add(shape)

        return list(cameras)

    def get_start_frame(self) -> int:
        """Gets the render start frame."""
        return int(self.start_frame)

    def save_file(self) -> bool:
        """Saves the file."""
        om.MGlobal.displayWarning(f'[{self.CLASS_NAME}] File must be saved.')

        result = cmds.confirmDialog(
            title='Export to Envy',
            message='Maya file must be save it to export to Envy.\nDo you want to save it?',
            button=['Yes', 'No'],
            defaultButton='Yes',
            cancelButton='No',
            dismissString='No')

        if result == 'Yes':
            cmds.file(save=True)
            return True
        else:
            om.MGlobal.displayError(f'[{self.CLASS_NAME}] Export to Envy aborted by the user. Maya file must be saved.')
            return False

    def set_allocation(self, allocation: int) -> None:
        """Sets the allocation."""
        self.allocation = allocation

    def set_end_frame(self, frame: int) -> None:
        """Sets the end frame."""
        self.end_frame = frame

    def set_start_frame(self, frame: int) -> None:
        """Sets the start frame."""
        self.start_frame = frame

    def set_tile_bounds(self, min: tuple, max: tuple) -> None:
        """Sets the minimum and maximum coordinates for a tile"""
        self.tile_bound_min = min
        self.tile_bound_max = max

    def set_tiled_rendering_settings(self, min_bound=(0, 0), max_bound=(100, 100), image_output_prefix='<Scene>/<RenderLayer>/<Camera>_000'):
        self.tiled_rendering = True
        self.tile_bound_min = min_bound
        self.tile_bound_max = max_bound
        self.image_output_prefix = image_output_prefix

    def set_arnold_settings(self) -> bool:
        """Sets Arnold settings."""
        save_file = False

        if cmds.getAttr('defaultArnoldRenderOptions.log_verbosity') != 2:
            cmds.setAttr('defaultArnoldRenderOptions.log_verbosity', 2)
            om.MGlobal.displayInfo(f'[{self.CLASS_NAME}] defaultArnoldRenderOptions.log_verbosity = 2.')
            save_file = True

        if cmds.getAttr('defaultArnoldRenderOptions.log_to_console') != 1:
            cmds.setAttr('defaultArnoldRenderOptions.log_to_console', 1)
            om.MGlobal.displayInfo(f'[{self.CLASS_NAME}] defaultArnoldRenderOptions.log_to_console = 1.')
            save_file = True

        return save_file

    def set_redshift_settings(self) -> bool:
        """Sets Redshift settings."""
        save_file = False

        if cmds.getAttr('redshiftOptions.logLevel') != 2:
            cmds.setAttr('redshiftOptions.logLevel', 2)
            om.MGlobal.displayInfo(f'[{self.CLASS_NAME}] redshiftOptions.logLevel = 2.')
            save_file = True

        return save_file

    def set_vray_settings(self) -> bool:
        """Sets V-Ray settings."""
        save_file = False

        if cmds.getAttr('vraySettings.sys_message_level') != 3:
            cmds.setAttr('vraySettings.sys_message_level', 3)
            om.MGlobal.displayInfo(f'[{self.CLASS_NAME}] vraySettings.sys_message_level = 3.')
            save_file = True

        if cmds.getAttr('vraySettings.sys_progress_increment') != 1:
            cmds.setAttr('vraySettings.sys_progress_increment', 1)
            om.MGlobal.displayInfo(f'[{self.CLASS_NAME}] vraySettings.sys_progress_increment = 1.')
            save_file = True

        return save_file


if __name__ == '__main__':
    maya_to_envy = MayaToEnvy()
