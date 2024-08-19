import os
import sys
import datetime
from envyJobs import job as ej
from envyJobs.enums import Purpose

directory = 'Z:/school/ENVY/__ENVYTEST__/'
if directory not in sys.path:
    sys.path.append(directory)
import __config__ as config
ENVYBINPATH = config.Config.REPOPATH
sys.path.append(ENVYBINPATH)


def createEnvyJobs(myNode):
    node = myNode
    saveFile = hou.ui.displayConfirmation('Save Hip File? \n(Otherwise hWedge could not work as intended)')
    if saveFile:
        hou.hipFile.save()
    else:
        return

    # get NVC
    NVC = myNode.parm('nvcToken').eval()
    job_name = myNode.parm('jobName').eval()

    # check if descriptive files checkbox is on
    generateDescriptiveFile = False
    nvNode = None

    if (myNode.parm('descriptiveFileBool').eval() == 1):
        generateDescriptiveFile = True

    # iterate over each job
    envyJobsMultiParm = myNode.parm('envyJobs')
    for i in range(envyJobsMultiParm.eval()):
        new_job = ej.Job(f'{job_name}_{str(i + 1).zfill(3)}')
        new_job.set_meta()
        environment = {}
        parameters = {}

        job_index = i + 1
        parameter_edits_multiparm = myNode.parm(f'parameterEdits{job_index}')
        button_to_press_parm = myNode.parm(f'targetButton{job_index}')

        # frame range toggle
        frame_range_toggle = myNode.parm(f'useJobFrameRange{job_index}')
        if frame_range_toggle.eval() == 1:
            # get frame range parms
            start_frame_parm_parm = node.parm(f'job_startFrameParm{job_index}')
            start_frame_value_parm = node.parm(f'job_startFrameValue{job_index}')
            end_frame_parm_parm = node.parm(f'job_endFrameParm{job_index}')
            end_frame_value_parm = node.parm(f'job_endFrameValue{job_index}')
            increment_parm_parm = node.parm(f'job_incrementFrameParm{job_index}')
            increment_value_parm = node.parm(f'job_incrementFrameValue{job_index}')

            # sanitize parms -----------------------------------------------------------------
            try:
                start_frame_parm = start_frame_parm_parm.getReferencedParm()
                end_frame_parm = end_frame_parm_parm.getReferencedParm()
                increment_parm = increment_parm_parm.getReferencedParm()
            except AttributeError:
                hou.ui.displayMessage(f'A frame range parameter is unfilled in job #{job_index}')
                return

            # check if start frame parm is valid
            if start_frame_parm == start_frame_parm_parm:
                hou.ui.displayMessage(
                    f"Invalid Parameter Reference: {start_frame_parm_parm.name()} ({start_frame_parm_parm.rawValue()})")
                return

            start_frame = start_frame_value_parm.eval()

            # check if start frame value is valid
            try:
                start_frame = int(start_frame)
            except ValueError:
                hou.ui.displayMessage(f"{start_frame_value_parm.name()} Must be set to an integer")
                return

            # end frame

            # check if end frame parm is valid
            if end_frame_parm == end_frame_parm_parm:
                hou.ui.displayMessage(
                    f"Invalid Parameter Reference: {end_frame_parm_parm.name()} ({end_frame_parm_parm.rawValue()})")
                return

            end_frame = end_frame_value_parm.eval()

            # check if end frame value is valid
            try:
                end_frame = int(end_frame)
            except ValueError:
                hou.ui.displayMessage(f"{end_frame_parm_value.name()} Must be set to an integer")
                return

            # increment

            # check if end frame parm is valid
            if increment_parm == increment_parm_parm:
                hou.ui.displayMessage(
                    f"Invalid Parameter Reference: {increment_parm_parm.name()} ({increment_parm_parm.rawValue()})")
                return

            increment = increment_value_parm.eval()

            # check if end frame value is valid
            try:
                increment = int(increment)
            except ValueError:
                hou.ui.displayMessage(f"{increment_value_parm.name()} Must be set to an integer")
                return

            # sanitize parms -----------------------------------------------------------------

            new_job.add_range(start_frame, end_frame, increment)
            new_job.set_purpose(Purpose.CACHE)

        # simulation toggle
        simulation_toggle = myNode.parm(f'useJobSimulation{job_index}')
        if simulation_toggle.eval() == 1:
            new_job.set_purpose(Purpose.SIMULATION)
            pass
            # todo implement simulation logic

        # validated button to press is good
        button_to_press = button_to_press_parm.getReferencedParm()
        if button_to_press_parm == button_to_press:
            hou.ui.displayMessage(f'Button_to_press is invalid for job #{job_index}')
            return

        # check if node is nvcache
        NV_cache = False
        NV_node = None
        NV_cache_dir = None
        if 'NVCACHE' in button_to_press.node().type().name().upper():
            NV_node = button_to_press.node()
            NV_cache = True

            if (NV_node.parm('filemethod').eval() == 1):  # then explicit is true
                NV_cache_dir = str(NV_node.parm('file').eval()).replace('\\', '/').split('/')
                NV_cache_dir.pop()
                NV_cache_dir = '/'.join(NV_cache_dir)

            else:  # explicit is false
                cacheNodeBaseName = str(NV_node.evalParm("basename"))
                cacheNodeSavePath = str(NV_node.evalParm("basedir"))
                cacheNodeVersion = str(NV_node.evalParm("NVversion"))
                NV_cache_dir = f"{cacheNodeSavePath}/{cacheNodeBaseName}/v{cacheNodeVersion}"

            # iterate over parameter edits

        # iterate over parameter edits
        for j in range(parameter_edits_multiparm.eval()):
            parameter_edit_index = j + 1
            parameter_parm_parm = node.parm(f'parm{job_index}_{parameter_edit_index}')
            value_parm = node.parm(f'value{job_index}_{parameter_edit_index}')

            # check that parameter_parm points to something
            parameter_parm = parameter_parm_parm.getReferencedParm()
            if parameter_parm_parm == parameter_parm:
                hou.ui.displayMessage(f"Invalid Parameter Reference: {parameter_parm_parm.name()} ({parameter_parm_parm.rawValue()})")
                return

            rawValueString = parameter_parm_parm.rawValue()
            rawValueStringReplaced = rawValueString.replace('$NVJ', str(job_index))
            rawValueStringReplaced = rawValueStringReplaced.replace('$NVC', str(NVC))
            parameter_parm_parm.set(rawValueStringReplaced)
            value = parameter_parm_parm.eval()
            parameter_parm_parm.set(rawValueString)

            try:
                value = float(value)
            except Exception:
                pass

            parameters[parameter_parm.path()] = value

        environment['HIP'] = node.parm('hip').eval()
        environment['JOB'] = node.parm('job').eval()

        new_job.set_environment(environment)
        new_job.set_parameters(parameters)
        new_job.set_type('PLUGIN_eHoudini')
        new_job.write()

def set_advanced_from_NVcache(node, multi_parm_index):
    button_to_press_parm = node.parm(f'targetButton{multi_parm_index}')

    # validated button to press is good
    button_to_press = button_to_press_parm.getReferencedParm()
    if button_to_press_parm == button_to_press:
        hou.ui.displayMessage(f'Button_to_press is invalid for job #{multi_parm_index}')
        return

    # check if node is nvcache
    NV_node = None
    NV_cache_dir = None
    if 'NVCACHE' not in button_to_press.node().type().name().upper():
        hou.ui.displayMessage(f'target buttom must be from an NVcache node -> job #{multi_parm_index}')
        return

    NV_node = button_to_press.node()

    if (NV_node.parm('filemethod').eval() == 1):  # then explicit is true
        NV_cache_dir = str(NV_node.parm('file').eval()).replace('\\', '/').split('/')
        NV_cache_dir.pop()
        NV_cache_dir = '/'.join(NV_cache_dir)

    else:  # explicit is false
        cacheNodeBaseName = str(NV_node.evalParm("basename"))
        cacheNodeSavePath = str(NV_node.evalParm("basedir"))
        cacheNodeVersion = str(NV_node.evalParm("NVversion"))
        NV_cache_dir = f"{cacheNodeSavePath}/{cacheNodeBaseName}/v{cacheNodeVersion}"

    start_frame_parm = NV_node.parm('f1')
    start_frame = start_frame_parm.eval()
    end_frame_parm = NV_node.parm('f2')
    end_frame = end_frame_parm.eval()
    increment_parm = NV_node.parm('f3')
    increment = int(increment_parm.eval())
    simulation = NV_node.parm('cachesim').eval()

    node.parm(f'useJobFrameRange{multi_parm_index}').set(1)
    node.parm(f'useJobSimulation{multi_parm_index}').set(simulation)

    start_frame_parm_parm = node.parm(f'job_startFrameParm{multi_parm_index}').set('`' + start_frame_parm.path() + '`')
    start_frame_value_parm = node.parm(f'job_startFrameValue{multi_parm_index}')
    start_frame_value_parm.deleteAllKeyframes()
    start_frame_value_parm.set(start_frame)
    end_frame_parm_parm = node.parm(f'job_endFrameParm{multi_parm_index}').set('`' + end_frame_parm.path() + '`')
    end_frame_value_parm = node.parm(f'job_endFrameValue{multi_parm_index}')
    end_frame_value_parm.deleteAllKeyframes()
    end_frame_value_parm.set(int(end_frame))
    increment_parm_parm = node.parm(f'job_incrementFrameParm{multi_parm_index}').set('`' + increment_parm.path() + '`')
    increment_value_parm = node.parm(f'job_incrementFrameValue{multi_parm_index}').set(increment)

