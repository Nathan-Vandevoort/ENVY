import sys
import os

directory = 'Z:/envy/'
plugin_directory = os.path.join(directory, 'Plugins')
utils_directory = os.path.join(directory, 'utils')
if directory not in sys.path:
    sys.path.append(directory)

if plugin_directory not in sys.path:
    sys.path.append(plugin_directory)

if utils_directory not in sys.path:
    sys.path.append(utils_directory)

import config_bridge as config

ENVYBINPATH = config.Config.REPOPATH
sys.path.append(ENVYBINPATH)
from envyRepo.envyJobs import job as ej
from envyRepo.envyJobs.enums import Purpose


def createSimulationEnvyJob(node):
    selection = hou.ui.displayCustomConfirmation('Save Hip File? \n(Otherwise hWedge could not work as intended)',
                                                 buttons=('Save and continue', 'Continue without saving', 'Cancel'),
                                                 suppress=hou.confirmType.BackgroundSave,
                                                 default_choice=0,
                                                 close_choice=2)
    if selection == 0:
        hou.hipFile.save()

    elif selection == 1:
        pass

    elif selection == 2:
        return

    is_simulation = node.parm('isSimulation').eval()

    job_name = node.parm('jobName').eval()
    parameter_edits_multiparm = node.parm('simulation_parameterEdits')
    is_resumable = node.parm('advanced_simulation_resumable')
    parameters = {}
    environment = {}
    simulation_param_names = {
        'f1': ('simulation_startParamName', 'simulation_startValue'),
        'f2': ('simulation_endParamName', 'simulation_endValue'),
        'substeps': ('simulation_substepsParamName', 'simulation_substepsValue'),
        'version': ('simulation_versionParamName', 'simulation_versionValue'),
    }

    #  get start frame values
    start_parm = node.parm(simulation_param_names['f1'][0])
    start_referenced_parm = start_parm.getReferencedParm()
    if start_parm == start_referenced_parm:
        hou.ui.displayMessage('Start Frame Parameter path invalid')
    start_frame = int(float(node.parm(simulation_param_names['f1'][1]).eval()))
    environment['Start_Frame'] = {start_referenced_parm.path(): start_frame}

    #  get end frame values
    end_parm = node.parm(simulation_param_names['f2'][0])
    end_referenced_parm = end_parm.getReferencedParm()
    if end_parm == end_referenced_parm:
        hou.ui.displayMessage('End Frame Parameter path invalid')
    end_frame = int(float(node.parm(simulation_param_names['f2'][1]).eval()))
    environment['End_Frame'] = {end_referenced_parm.path(): end_frame}

    # get substeps values
    substeps_parm = node.parm(simulation_param_names['substeps'][0])
    susbteps_referenced_parm = substeps_parm.getReferencedParm()
    if substeps_parm == susbteps_referenced_parm:
        hou.ui.displayMessage('Substeps Parameter path invalid')
    substeps = float(node.parm(simulation_param_names['substeps'][1]).eval())
    environment['Substeps'] = {susbteps_referenced_parm.path(): substeps}

    # get version values
    version_parm = node.parm(simulation_param_names['version'][0])
    version_referenced_parm = version_parm.getReferencedParm()
    if version_parm == version_referenced_parm:
        hou.ui.displayMessage('Version Parameter path invalid')
    version = float(node.parm(simulation_param_names['version'][1]).eval())
    environment['Version'] = {version_referenced_parm.path(): version}

    target_button = node.parm('simulation_targetButton').getReferencedParm()
    environment['Target_Button'] = target_button.path()
    parameter_edits = dictFromParameterEdits(node, parameter_edits_multiparm, 'simulation_', 1)
    if parameter_edits is None:
        return
    parameters.update(parameter_edits)
    environment['HIP'] = hou.hipFile.path()
    environment['JOB'] = hou.getenv('JOB')
    environment['Job_Type'] = 'cache'

    if is_simulation is 1:
        environment['Job_Type'] = 'simulation'
        if is_resumable.eval() == 1:

            dopnet_parm = node.parm('advanced_simulation_dopNetwork')
            try:
                dopnet_node = dopnet_parm.evalAsNode()
            except TypeError:
                hou.ui.displayMessage(f'Dopnet parameter must be the path to a dopnet. {dopnet_parm.rawValue()}')
                return

            initial_state_parm = node.parm('advanced_simulation_initialState')
            initial_state = initial_state_parm.getReferencedParm()
            if initial_state_parm == initial_state:
                hou.ui.displayMessage(f'Initial State parameter invalid: {initial_state_parm.eval()}')
                return

            dopnet_start_frame_parm = node.parm('advanced_simulation_startFrame')
            dopnet_start_frame = dopnet_start_frame_parm.getReferencedParm()
            if dopnet_start_frame == dopnet_start_frame_parm:
                hou.ui.displayMessage(f'Dopnet start frame parameter invalid: {dopnet_start_frame_parm.eval()}')
                return

            checkpoint_file_path_parm = node.parm('advanced_simulation_checkpointFilePath')
            checkpoint_file_path = checkpoint_file_path_parm.getReferencedParm()
            if checkpoint_file_path == checkpoint_file_path_parm:
                hou.ui.displayMessage(f'Checkpoint File Path invalid: {checkpoint_file_path_parm.eval()}')
                return

            checkpoint_trail_length_parm = node.parm('advanced_simulation_checkpointTrailLength')
            checkpoint_trail_length = checkpoint_trail_length_parm.getReferencedParm()
            if checkpoint_trail_length == checkpoint_trail_length_parm:
                hou.ui.displayMessage(f'Checkpoint Trail Length Path invalid: {checkpoint_trail_length_parm.eval()}')
                return

            checkpoint_interval_parm = node.parm('advanced_simulation_checkpointInterval')
            checkpoint_interval = checkpoint_interval_parm.getReferencedParm()
            if checkpoint_interval == checkpoint_interval_parm:
                hou.ui.displayMessage(f'Checkpoint Interval Path invalid: {checkpoint_interval_parm.eval()}')
                return

            checkpoint_file_path_value_parm = node.parm('advanced_simulation_checkpointFilePath_value')
            checkpoint_file_path_value = checkpoint_file_path_value_parm.rawValue()
            checkpoint_file_path_value = checkpoint_file_path_value.replace('$OS', dopnet_node.name())
            checkpoint_file_path_value_parm.set(checkpoint_file_path_value)
            checkpoint_file_path_value = checkpoint_file_path_value_parm.eval()
            checkpoint_file_path_value = f'{checkpoint_file_path_value}$HIPNAME.$OS.$JOBID.$STARTFRAMETOKEN.$SF4.sim'
            checkpoint_file_path = (
                checkpoint_file_path.path(),
                checkpoint_file_path_value
            )

            checkpoint_trail_length_value_parm = node.parm('advanced_simulation_checkpointTrailLength_value')
            checkpoint_trail_length_value = checkpoint_trail_length_value_parm.eval()
            checkpoint_trail_length = (
                checkpoint_trail_length.path(),
                checkpoint_trail_length_value
            )

            checkpoint_interval_value_parm = node.parm('advanced_simulation_checkpointInterval_value')
            checkpoint_interval_value = checkpoint_interval_value_parm.eval()
            checkpoint_interval = (
                checkpoint_interval.path(),
                checkpoint_interval_value
            )

            environment['Job_Type'] = 'resumable_simulation'
            environment['Dopnet_Initial_State_Parm'] = initial_state.path()
            environment['Dopnet_Start_Frame_Parm'] = dopnet_start_frame.path()
            environment['Checkpoint_File_Path'] = checkpoint_file_path
            environment['Checkpoint_Trail_Length'] = checkpoint_trail_length
            environment['Checkpoint_Interval'] = checkpoint_interval
            environment['$OS'] = dopnet_node.name()

    new_job = ej.Job(f'{job_name}_{str(1).zfill(3)}')
    new_job.set_meta()
    job_id = new_job.get_id()
    environment['Job_Id'] = job_id

    if is_simulation is True:
        new_job.set_environment(environment)
        new_job.set_parameters(parameters)
        new_job.set_type('PLUGIN_eHoudini')
        new_job.set_purpose(Purpose.SIMULATION)
        new_job.add_range(start_frame, end_frame, 1)
        new_job.set_allocation((end_frame + 1) - start_frame)
        new_job.write()

    else:
        new_job.set_environment(environment)
        new_job.set_parameters(parameters)
        new_job.set_type('PLUGIN_eHoudini')
        new_job.set_purpose(Purpose.CACHE)
        new_job.add_range(start_frame, end_frame, 1)
        new_job.set_allocation(node.parm('allocationSize').eval())
        new_job.write()


def dictFromParameterEdits(node, parameter_edits_multiparm: hou.parm, parm_namespace: str,
                           job_index: int) -> dict | None:
    NVC = node.parm('nvcToken').eval()
    parameters = {}
    for j in range(parameter_edits_multiparm.eval()):
        parameter_edit_index = j + 1
        parameter_parm_parm = node.parm(f'{parm_namespace}parm{job_index}_{parameter_edit_index}')
        value_parm = node.parm(f'{parm_namespace}value{job_index}_{parameter_edit_index}')

        # check that parameter_parm points to something
        parameter_parm = parameter_parm_parm.getReferencedParm()
        if parameter_parm_parm == parameter_parm:
            hou.ui.displayMessage(
                f"Invalid Parameter Reference: {parameter_parm_parm.name()} ({parameter_parm_parm.rawValue()})")
            return None

        rawValueString = value_parm.rawValue()
        rawValueStringReplaced = rawValueString.replace('$NVJ', str(job_index))
        rawValueStringReplaced = rawValueStringReplaced.replace('$NVC', str(NVC))
        value_parm.set(rawValueStringReplaced)
        value = value_parm.eval()
        value_parm.set(rawValueString)

        try:
            value = float(value)
        except Exception:
            pass

        parameters[parameter_parm.path()] = value
    return parameters


def setSimulationParametersFromNode(node):
    cache_node = node
    if cache_node is None:
        hou.ui.displayMessage(f'Cannot find node at given Cache Node path')
        return

    target_button_parm = node.parm('simulation_targetButton')

    start_frame_parm = node.parm('simulation_startParamName')
    start_frame_value_parm = node.parm('simulation_startValue')

    end_frame_parm = node.parm('simulation_endParamName')
    end_frame_value_parm = node.parm('simulation_endValue')

    substeps_parm = node.parm('simulation_substepsParamName')
    substeps_value_parm = node.parm('simulation_substepsValue')

    version_parm = node.parm('simulation_versionParamName')
    version_value_parm = node.parm('simulation_versionValue')

    #  Target Button
    target_button_parm.revertToDefaults()
    target_button_parm.deleteAllKeyframes()
    file_cache_target_button = cache_node.parm('execute')
    target_button_parm.set(f"`ch('{file_cache_target_button.path()}')`", language=hou.exprLanguage.Hscript,
                           follow_parm_reference=False)

    #  Start Frame
    start_frame_parm.revertToDefaults()
    start_frame_value_parm.revertToDefaults()
    start_frame_parm.deleteAllKeyframes()
    start_frame_value_parm.deleteAllKeyframes()
    file_cache_start_frame_parm = cache_node.parm('f1')
    start_frame_parm.set(f"`ch('{file_cache_start_frame_parm.path()}')`", language=hou.exprLanguage.Hscript,
                         follow_parm_reference=False)
    start_frame_value_parm.set(file_cache_start_frame_parm.evalAsString())

    #  End Frame
    end_frame_parm.revertToDefaults()
    end_frame_value_parm.revertToDefaults()
    end_frame_parm.deleteAllKeyframes()
    end_frame_value_parm.deleteAllKeyframes()
    file_cache_end_frame_parm = cache_node.parm('f2')
    end_frame_parm.set(f"`ch('{file_cache_end_frame_parm.path()}')`", language=hou.exprLanguage.Hscript,
                       follow_parm_reference=False)
    end_frame_value_parm.set(file_cache_end_frame_parm.evalAsString())

    #  Substeps
    substeps_parm.revertToDefaults()
    substeps_value_parm.revertToDefaults()
    substeps_parm.deleteAllKeyframes()
    substeps_value_parm.deleteAllKeyframes()
    file_cache_substeps_parm = cache_node.parm('substeps')
    substeps_parm.set(f"`ch('{file_cache_substeps_parm.path()}')`", language=hou.exprLanguage.Hscript,
                      follow_parm_reference=False)
    substeps_value_parm.set(file_cache_substeps_parm.evalAsString())

    #  Version
    version_parm.revertToDefaults()
    version_value_parm.revertToDefaults()
    version_parm.deleteAllKeyframes()
    version_value_parm.deleteAllKeyframes()
    file_cache_version_parm = cache_node.parm('substeps')
    version_parm.set(f"`ch('{file_cache_version_parm.path()}')`", language=hou.exprLanguage.Hscript,
                     follow_parm_reference=False)
    version_value_parm.set(file_cache_version_parm.evalAsString())


def createGenericEnvyJobs(myNode):
    node = myNode
    saveFile = hou.ui.displayConfirmation('Save Hip File? \n(Otherwise hWedge could not work as intended)')
    if saveFile:
        hou.hipFile.save()
    else:
        return

    # get NVC
    NVC = myNode.parm('nvcToken').eval()
    job_name = myNode.parm('jobName').eval()

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

        job_index = i + 1
        parameter_edits_multiparm = myNode.parm(f'parameterEdits{job_index}')
        button_to_press_parm = myNode.parm(f'targetButton{job_index}')

        # validated button to press is good
        button_to_press = button_to_press_parm.getReferencedParm()
        if button_to_press_parm == button_to_press:
            hou.ui.displayMessage(f'Button_to_press is invalid for job #{job_index}')
            return

        environment['Target_Button'] = button_to_press.path()

        # check if node is nvcache
        NV_cache = False
        NV_node = None
        NV_cache_dir = None
        if 'NVCACHE' in button_to_press.node().type().name().upper():
            NV_node = button_to_press.node()
            NV_cache = True

            if NV_node.parm('filemethod').eval() == 1:  # then explicit is true
                NV_cache_dir = str(NV_node.parm('file').eval()).replace('\\', '/').split('/')
                NV_cache_dir.pop()
                NV_cache_dir = '/'.join(NV_cache_dir)

            else:  # explicit is false
                cacheNodeBaseName = str(NV_node.evalParm("basename"))
                cacheNodeSavePath = str(NV_node.evalParm("basedir"))
                cacheNodeVersion = str(NV_node.evalParm("NVversion"))
                NV_cache_dir = f"{cacheNodeSavePath}/{cacheNodeBaseName}/v{cacheNodeVersion}"

            # iterate over parameter edits

        parameters = dictFromParameterEdits(myNode, parameter_edits_multiparm, '', job_index)
        if parameters is None:
            return

        environment['HIP'] = hou.hipFile.path()
        environment['JOB'] = hou.getenv('JOB')
        environment['Job_Type'] = 'generic'

        new_job.set_environment(environment)
        new_job.set_parameters(parameters)
        new_job.set_type('PLUGIN_eHoudini')
        new_job.set_purpose(Purpose.CACHE)
        new_job.add_range(1, 1, 1)
        new_job.write()


def duplicateJob(myNode, parm, multiParmIndex):
    jobParm = parm.parentMultiParm()
    children = jobParm.multiParmInstances()
    parmIndex = parm.multiParmInstanceIndices()

    # isolate parms in my multiparm block
    targetButton = myNode.parm(f'targetButton{multiParmIndex}')
    parameterEdits = myNode.parm(f'parameterEdits{multiParmIndex}')

    # raise an error if target button or parameter edits cannot be found
    if targetButton == None or parameterEdits == None:
        hou.ui.displayMessage(f"Failed to duplicate tab")
        return

    # get the list of parameter edit parms
    parameterEdits = parameterEdits.multiParmInstances()

    # convert parameter edits into a dict of parameter and its value
    parameterEditsDict = {}
    for index, param in enumerate(parameterEdits):
        # skip every other index because we are assuming that there are only parameter and value
        if index % 2 != 0:
            continue

        # add to list
        parameterEditsDict[param] = parameterEdits[index + 1]

    # Make a new job
    newJobIndex = jobParm.eval()
    jobParm.insertMultiParmInstance(newJobIndex)
    newJobIndex += 1

    # isolate parms in new multiparm
    newTargetButton = myNode.parm(f'targetButton{newJobIndex}')
    newParameterEdits = myNode.parm(f'parameterEdits{newJobIndex}')

    # raise an error if target button or parameter edits cannot be found
    if newTargetButton == None or newParameterEdits == None:
        hou.ui.displayMessage(f"Failed to duplicate tab")
        return

    # set new target button
    newTargetButton.set(targetButton.rawValue())

    # set new parameter edits
    for param in parameterEditsDict:
        # make a new parameter edit
        newParameterEdits.insertMultiParmInstance(newParameterEdits.evalAsInt())
        newParamIndex = newParameterEdits.evalAsInt()

        # iterate over new params to get parameter objects
        targetParmParm = None
        targetValueParm = None
        for createdParam in newParameterEdits.multiParmInstances():
            # if param is not of the right index then ignore it
            newParamEditsChildren = createdParam.multiParmInstanceIndices()
            if newParamEditsChildren[len(newParamEditsChildren) - 1] == newParamIndex:

                # if the name is parm then set it to targetParmParm
                if 'parm' in createdParam.name():
                    targetParmParm = createdParam

                # if the name is value then set it  targetParmValue
                if 'value' in createdParam.name():
                    targetValueParm = createdParam

        # raise an error if parameters were not found
        if targetParmParm == None or targetValueParm == None:
            hou.ui.displayMessage(f"Failed to duplicate tab")
            return

        # set Parm to Parm from dict
        targetParmParm.set(param.rawValue())

        # set Value to Value from dict
        targetValueParm.set(parameterEditsDict[param].rawValue())


def configureDopnet(node):
    dopnet_parm = node.parm('advanced_simulation_dopNetwork')

    try:
        dopnet_node = dopnet_parm.evalAsNode()
    except TypeError:
        hou.ui.displayMessage(f'Dopnet parameter must be the path to a dopnet. {dopnet_parm.rawValue()}')
        return

    if dopnet_node is None:
        hou.ui.displayMessage(f'Dopnet parameter must be the path to a single dopnet. {dopnet_parm.rawValue()}')
        return

    # enable checkpoint on dopnet
    dopnet_node.parm('cacheenabled').set(1)


def setAdvancedSimulationResumableSettings(node):
    dopnet_parm = node.parm('advanced_simulation_dopNetwork')
    dopnet_parm.deleteAllKeyframes()

    initial_state_parm = node.parm('advanced_simulation_initialState')
    initial_state_parm.revertToDefaults()

    dopnet_start_frame_parm = node.parm('advanced_simulation_startFrame')
    dopnet_start_frame_parm.revertToDefaults()

    checkpoint_file_path_parm = node.parm('advanced_simulation_checkpointFilePath')
    checkpoint_file_path_parm.revertToDefaults()

    checkpoint_trail_length_parm = node.parm('advanced_simulation_checkpointTrailLength')
    checkpoint_trail_length_parm.revertToDefaults()

    checkpoint_interval_parm = node.parm('advanced_simulation_checkpointInterval')
    checkpoint_interval_parm.revertToDefaults()

    try:
        dopnet_node = dopnet_parm.evalAsNode()
    except TypeError:
        hou.ui.displayMessage(f'Dopnet parameter must be the path to a dopnet. {dopnet_parm.rawValue()}')
        return

    if dopnet_node is None:
        hou.ui.displayMessage(f'Dopnet parameter must be the path to a single dopnet. {dopnet_parm.rawValue()}')
        return

    # get dopnet initial state param
    dopnet_initial_state = dopnet_node.parm('initialstate')
    dopnet_initial_state.deleteAllKeyframes()
    initial_state_parm.set(f"`chs('{dopnet_initial_state.path()}')`", language=hou.exprLanguage.Hscript,
                           follow_parm_reference=False)

    # get dopnet start frame parm
    dopnet_start_frame = dopnet_node.parm('startframe')
    dopnet_start_frame.deleteAllKeyframes()
    dopnet_start_frame_parm.set(f"`chs('{dopnet_start_frame.path()}')`", language=hou.exprLanguage.Hscript,
                                follow_parm_reference=False)

    # get checkpoint file param
    dopnet_checkpoint_file = dopnet_node.parm('explicitcachename')
    dopnet_checkpoint_file.deleteAllKeyframes()
    checkpoint_file_path_parm.set(f"`chs('{dopnet_checkpoint_file.path()}')`", language=hou.exprLanguage.Hscript,
                                  follow_parm_reference=False)

    # get checkpoint trail length parm
    dopnet_trail_length = dopnet_node.parm('explicitcachensteps')
    dopnet_trail_length.deleteAllKeyframes()
    checkpoint_trail_length_parm.set(f'`chs("{dopnet_trail_length.path()}")`', language=hou.exprLanguage.Hscript,
                                     follow_parm_reference=False)

    # get checkpoint interval
    dopnet_checkpoint_interval = dopnet_node.parm('explicitcachecheckpointspacing')
    dopnet_checkpoint_interval.deleteAllKeyframes()
    checkpoint_interval_parm.set(f"`chs('{dopnet_checkpoint_interval.path()}')`", language=hou.exprLanguage.Hscript,
                                 follow_parm_reference=False)


def modifyVersion(node, amount):
    versionParm = node.parm('version')
    versionParm.set(versionParm.eval() + amount)
    versionParm.pressButton()


def setRange(kwargs):
    node = kwargs['node']

    parm = kwargs['parm']
    r1 = node.parm("f1")
    r2 = node.parm("f2")
    r3 = node.parm("f3")
    ss = node.parm("substeps")

    if parm.evalAsString() == "fstartend":
        r1.deleteAllKeyframes()
        r2.deleteAllKeyframes()
        r1.setExpression('$FSTART')
        r2.setExpression('$FEND')
    elif parm.evalAsString() == "rfstartend":
        r1.deleteAllKeyframes()
        r2.deleteAllKeyframes()
        r1.setExpression('$RFSTART')
        r2.setExpression('$RFEND')
    elif parm.evalAsString() == "nosubsteps":
        r3.deleteAllKeyframes()
        r3.set(1)
        node.parm("substeps").set(1)
    elif parm.evalAsString() == "substeps2":
        r3.deleteAllKeyframes()
        r3.set(1)
        ss.deleteAllKeyframes()
        ss.set(2)
    elif parm.evalAsString() == "substeps4":
        r3.deleteAllKeyframes()
        r3.set(1)
        ss.deleteAllKeyframes()
        ss.set(4)
    elif parm.evalAsString() == "substeps5":
        r3.deleteAllKeyframes()
        r3.set(1)
        ss.deleteAllKeyframes()
        ss.set(5)
    elif parm.evalAsString() == "every2":
        r3.deleteAllKeyframes()
        r3.set(2)
        ss.set(1)
    elif parm.evalAsString() == "every5":
        r3.deleteAllKeyframes()
        r3.set(5)
        ss.set(1)
    elif parm.evalAsString() == "every10":
        r3.deleteAllKeyframes()
        r3.set(10)
        ss.set(1)


def setExpressionParm(_parm_from, _parm_to):
    node_from = _parm_from.node()
    node_to = _parm_to.node()

    relative_path = node_to.relativePathTo(node_from)

    parm_template = _parm_from.parmTemplate()

    chref = "ch"
    if (parm_template.type() == hou.parmTemplateType.String):
        chref = "chs"

    expression = '%s("%s/%s")' % (chref, relative_path, _parm_from.name())
    _parm_to.setExpression(expression)


def setRelativePath(_node_from, _parm_to):
    node_to = _parm_to.node()
    relative_path = node_to.relativePathTo(_node_from)

    _parm_to.set(relative_path)


def copyNodeWithNameRef(kwargs):
    node = kwargs["node"]

    copied = hou.copyNodesTo([node], node.parent())[0]
    copied.setPosition(node.position() + hou.Vector2(4, 0))
    setExpressionParm(node.parm("basename"), copied.parm("basename"))
    copied.parm("loadfromdisk").set(True)

    copied.setGenericFlag(hou.nodeFlag.Display, True)
    copied.setGenericFlag(hou.nodeFlag.Render, True)
    copied.setCurrent(True, True)


def quickSetups(kwargs):
    selected = kwargs["script_value"]

    if selected == "copy":
        copyNodeWithNameRef(kwargs)

    kwargs['parm'].set(0)


def hardenBaseName(node):
    if node.evalParm('hardenbasename') and node.evalParm('filemethod') == 0:
        if node.parm('basename').rawValue() != node.parm('basename').evalAsString():
            basename = node.parm('basename').evalAsString()
            node.parm('basename').deleteAllKeyframes()
            node.parm('basename').revertToDefaults()
            node.parm('basename').set(basename)


def enableLoadFromDisk(node):
    if node.evalParm('loadfromdiskonsave'):
        node.parm('loadfromdisk').set(1)


def saveToDisk(kwargs, filecache_node):
    # print(type(filecache_node.node('render').parm('execute')))
    filecache_node.node('render').parm('execute').pressButton()

    # kwargs['node'] is the top-level node, e.g. if this is wrapped in an HDA
    node = kwargs['node']
    hardenBaseName(node)
    enableLoadFromDisk(node)
    node.parm('reload').pressButton()


def saveToDiskInBackground(kwargs):
    import nodegraphtopui

    node = kwargs['node']

    nodegraphtopui.dirtyAll(kwargs['node'].parm('targettopnetwork').evalAsNode(), False)
    nodegraphtopui.cookOutputNode(kwargs['node'].parm('targettopnetwork').evalAsNode())

    hardenBaseName(node)
    enableLoadFromDisk(node)


def cancelCook(kwargs):
    import nodegraphtopui
    node = kwargs['node']
    nodegraphtopui.dirtyAll(node.parm('targettopnetwork').evalAsNode(), False)


def getOpenCommand(filepath):
    import platform

    OS = platform.system().lower()

    if 'windows' in OS:
        opener = 'start'
    elif 'osx' in OS or 'darwin' in OS:
        opener = 'open'
    else:
        opener = 'xdg-open'
    return '{opener} {filepath}'.format(opener=opener, filepath=filepath)


def openPath(kwargs):
    import os

    node = kwargs['node']

    dir = node.evalParm("basedir")
    if node.evalParm("filemethod"):
        dir = os.path.dirname(node.evalParm("file"))

    if os.path.exists(dir):
        if dir[-1] != '/':
            dir += '/'
        hou.ui.showInFileBrowser(dir)
    else:
        hou.ui.displayMessage(text="Could not open directory:\n{dir}.".format(dir=dir),
                              severity=hou.severityType.ImportantMessage)


def verBump(kwargs, operation='add'):
    node = kwargs['node']

    if 'add' in operation:
        node.parm("ver").set(node.evalParm("ver") + 1)
    else:
        node.parm("ver").set(max(node.evalParm("ver") - 1, 1))


def subverBump(kwargs, operation='add'):
    node = kwargs['node']

    if 'add' in operation:
        node.parm("subver").set(node.evalParm("subver") + 1)
    else:
        node.parm("subver").set(max(node.evalParm("subver") - 1, 0))


def setLatestVersion(node):
    cacheNodeBaseName = str(node.evalParm("basename"))
    cacheNodeSavePath = str(node.evalParm("basedir"))
    cacheNodeVersion = str(node.evalParm("NVversion"))

    versionDir = cacheNodeSavePath + '/' + cacheNodeBaseName

    # if version folder doesnt exist
    if os.path.isdir(versionDir) == False:
        node.parm('NVversion').set(1)
        return

    else:
        files = os.listdir(versionDir)

        # sort through files to get most recent version
        latestVersion = 0
        for file in files:
            file = file.split('/')
            file = file.pop()

            if file[0].upper() != 'V':
                continue

            version = 0
            try:
                version = int(file[1:])
            except ValueError:
                continue

            if version > latestVersion:
                latestVersion = version
        node.parm('NVversion').set(latestVersion + 1)

