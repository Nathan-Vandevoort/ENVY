import os
import datetime
import envyJobs as ej


def createEnvyJobs(myNode):
    saveFile = hou.ui.displayConfirmation('Save Hip File? \n(Otherwise hWedge could not work as intended)')
    if saveFile:
        hou.hipFile.save()
    else:
        return

    # get NVC
    NVC = myNode.parm('nvcToken').eval()

    # check if descriptive files checkbox is on
    generateDescriptiveFile = False
    nvNode = None

    if (myNode.parm('descriptiveFileBool').eval() == 1):
        generateDescriptiveFile = True

    # check if each parm in the multiparm is a valid parm
    envyJobsMultiParm = myNode.parm('envyJobs')
    jobsDict = {}
    descriptiveFilePathsDict = {}
    for i, job in enumerate(envyJobsMultiParm.multiParmInstances()):
        parmObject = job.getReferencedParm()

        # skip iteration if the parm is the parameter edit multiparm
        if 'parameterEdits' in parmObject.name():
            continue

        # skip if parm is duplicate job button
        if 'duplicateJob' in parmObject.name():
            continue

        # check if parm is valid
        if job == parmObject:
            parmName = job.name()
            hou.ui.displayMessage(f"Invalid Parameter Reference: {parmName} ({job.rawValue()})")
            return

        # check subparms
        editedParms = {'HIP': hou.hipFile.path(),
                       'JOB': hou.getenv('JOB')}
        parameterEditMultiParm = envyJobsMultiParm.multiParmInstances()[i + 1]

        # make sure that there actually are subparms
        parmsList = parameterEditMultiParm.multiParmInstances()

        for j, parm in enumerate(parmsList):
            subParmObject = parm.getReferencedParm()

            # skip iteration if the subparm is a value
            if 'value' in subParmObject.name():
                continue

            # check if parm is valid
            if parm == subParmObject:
                parmName = parm.name()
                hou.ui.displayMessage(f"Invalid Parameter Reference: {parmName} ({parm.rawValue()})")

            # append to editedParmsDict
            rawValueString = parameterEditMultiParm.multiParmInstances()[j + 1].rawValue()
            rawValueStringReplaced = rawValueString.replace('$NVJ', str((i / 3) + 1))
            rawValueStringReplaced = rawValueStringReplaced.replace('$NVC', str(NVC))
            parameterEditMultiParm.multiParmInstances()[j + 1].set(rawValueStringReplaced)
            value = parameterEditMultiParm.multiParmInstances()[j + 1].eval()
            parameterEditMultiParm.multiParmInstances()[j + 1].set(rawValueString)

            # cast value to float if able
            try:
                value = float(value)
            except Exception:
                pass
            editedParms[subParmObject.path()] = value

        # append job to jobsList
        jobsDict['Job' + str(int(i / 2)).zfill(3)] = [parmObject.path(), editedParms]

        # if generateDescriptiveFile is true
        nvCacheDir = None
        if generateDescriptiveFile == True:

            # check if node type is correct
            if 'NVCACHE' in parmObject.node().type().name().upper():
                nvNode = parmObject.node()

                # get the output path regardless if node is explicit or not
            if nvNode != None:

                # check if explicit or not
                if (nvNode.parm('filemethod').eval() == 1):  # then explicit is true
                    nvCacheDir = str(nvNode.parm('file').eval()).replace('\\', '/').split('/')
                    nvCacheDir.pop()
                    nvCacheDir = '/'.join(nvCacheDir)

                else:  # explicit is false
                    cacheNodeBaseName = str(nvNode.evalParm("basename"))
                    cacheNodeSavePath = str(nvNode.evalParm("basedir"))
                    cacheNodeVersion = str(nvNode.evalParm("NVversion"))

                    """
                    rawValueString = str(nvNode.parm('NVversion').rawValue())
                    versionSubstitute = rawValueString.replace('$NVJ', str((i / 3) + 1))
                    nvNode.parm('NVversion').set(versionSubstitute)
                    nvNode.parm('NVversion').set(rawValueString)
                    """

                    # This is a pretty terrible solution for updating the version on NV cache
                    originalVersion = nvNode.parm('NVversion').eval()
                    for parm in editedParms:

                        if 'NVversion' in parm:

                            # substitute NVJ token
                            rawValueString = str(editedParms[parm])
                            rawValueStringReplaced = rawValueString.replace('$NVJ', str((i / 3) + 1))
                            rawValueStringReplaced = rawValueStringReplaced.replace('$NVC', str(NVC))
                            value = eval(rawValueStringReplaced)

                            try:
                                cacheNodeVersion = int(value)
                            except Exception as err:
                                hou.ui.displayMessage(f"NVcache Version must be an integer\n{str(err)}")

                    nvCacheDir = f"{cacheNodeSavePath}/{cacheNodeBaseName}/v{cacheNodeVersion}"

                # check if directory exists if not make it
                if os.path.isdir(nvCacheDir) == False:
                    os.makedirs(nvCacheDir)

            descriptiveFilePathsDict['Job' + str(int(i / 2)).zfill(3)] = nvCacheDir

    # write out jobs to disk
    jobOutputPath = myNode.parm('jobOutputPath').eval()

    # make sure that jobOutputPath exists and make it if it doesnt
    if os.path.isdir(jobOutputPath) == False:
        os.makedirs(jobOutputPath)
        print(f'{jobOutputPath} did not exist Created {jobOutputPath}')

    jobName = myNode.parm('jobName').eval()
    import json
    descriptiveFileCounter = 0
    for i, job in enumerate(jobsDict):
        # create .NV file
        with open(f"{jobOutputPath}{jobName}_Wedge{i + NVC}.json", 'w') as outfile:
            json.dump({'Purpose': 'EnvyHWedge', job: jobsDict[job]}, outfile)
            outfile.close()

        # create json file if generateDescriptiveFile == true
        if generateDescriptiveFile == True and descriptiveFilePathsDict[job] != None:
            with open(f"{descriptiveFilePathsDict[job]}/{jobName}_descriptiveFile.json", 'w') as outfile:
                writeDict = {'TIME': datetime.datetime.now().strftime("%m-%d-%Y %H:%M"),
                             'BUTTONNODE': jobsDict[job][0],
                             'PARMS': jobsDict[job][1]
                             }
                json.dump(writeDict, outfile)
                outfile.close()
            descriptiveFileCounter += 1

    print('Jobs Submitted Succesfully!')
    print(f'Generated {descriptiveFileCounter} descriptive files')


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
    jobParm.insertMultiParmInstance(jobParm.evalAsInt())
    newJobIndex = jobParm.evalAsInt()

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


def makeMissingJobs(node):
    cacheDir = node.parm('cacheDir').eval()
    use_substeps = node.parm('substeps').eval()
    number_of_substeps = node.parm('numSubsteps').eval()
    consolidate_jobs = node.parm('consolidateJobs').eval()
    max_frames_per_job = node.parm('maxRangePerJob').eval()
    start_frame = node.parm('frameRangex').eval()
    end_frame = node.parm('frameRangey').eval()
    button_to_press_parm = node.parm('buttonToPress')
    start_frame_parm = node.parm('startFrameParm')
    end_frame_parm = node.parm('endFrameParm')

    if use_substeps == 0:
        number_of_substeps = 1

    # get user input parms
    button_to_press_referenced_parm = button_to_press_parm.getReferencedParm()
    if button_to_press_parm == button_to_press_referenced_parm:
        hou.ui.displayMessage(f'invalid path to button {button_to_press_parm.rawValue()}')

    start_frame_referenced_parm = start_frame_parm.getReferencedParm()
    if start_frame_referenced_parm == start_frame_parm:
        hou.ui.displayMessage(f'invalid path to start frame parm {start_frame_parm.rawValue()}')

    end_frame_referenced_parm = end_frame_parm.getReferencedParm()
    if end_frame_referenced_parm == end_frame_parm:
        hou.ui.displayMessage(f'invalid path to end frame parm {end_frame_parm.rawValue()}')

    # if max_frames_per_job is 0 then set it to a really large number
    if max_frames_per_job == 0:
        max_frames_per_job = 999999998

    elif max_frames_per_job == 1:
        max_frames_per_job = 2

    # max_frames_per_job up by 1 so it works as expected
    max_frames_per_job += 1

    # check if cache dir exists
    if not os.path.isdir(cacheDir):
        hou.ui.displayMessage(f'Cache directory does not exist: {cacheDir}')
        return

    # get all files in the cache directory
    files = os.listdir(cacheDir)

    sanitized_files = []
    descriptive_file = None
    # iterate over files and sanitize
    for file in files:
        path = cacheDir + file

        # skip if file is a directory
        if os.path.isdir(path):
            continue

        # check to see if file is descriptive file
        if '_descriptiveFile' in file:
            descriptive_file = file
            continue

        # get the frame number
        file_split = file.split('.')
        number_of_tokens = len(file_split) - 1
        value = None
        for i in range(number_of_tokens):

            # for not substeps
            if use_substeps == 0:
                # try to cast the token to an int
                try:
                    frame = int(file_split[number_of_tokens - i])
                    value = frame
                    break

                # if you cannot be casted you are not the frame number so skip
                except ValueError:
                    continue

                # if frame is none something went wrong so just skip that file
                if not frame:
                    continue

            # use substeps
            else:
                # try to cast the token to an int
                try:
                    frame = int(file_split[number_of_tokens - (i + 1)])
                    substep = float('.' + file_split[number_of_tokens - i])
                    value = frame + substep
                    break

                # if you cannot be casted you are not the frame number so skip
                except ValueError:
                    continue

                # if frame is none something went wrong so just skip that file
                if not frame:
                    continue

        sanitized_files.append(value)
    """  
    REMEMBER when using substeps if you need frames 1001-1004.5
    you need to set the end frame for that job to be 1005 or it will only go to 1004
    """
    # find missing frames
    missing_frames = []
    for i in range(((end_frame + 1) - start_frame) * number_of_substeps):
        value = start_frame + (i / number_of_substeps)

        if value not in sanitized_files:
            missing_frames.append(value)

        # stop iterating when value is end frame
        if value == float(end_frame):
            break

    tmp = []
    # consolidate missing frames to remove substeps and add one if the needed frame is a substep
    # make it so you can cluster them by a maximum amount of thingies
    for frame in missing_frames:

        if frame.is_integer():
            value = int(frame)
            if value not in tmp:
                tmp.append(value)

        else:
            value = int(frame) + 1
            if value not in tmp:
                tmp.append(value)
    missing_frames = tmp

    consolidated_frames = []
    # consolidate jobs if needed
    if consolidate_jobs == 1:
        i = 0
        counter = 0
        while i < len(missing_frames):
            j = i
            while j < len(missing_frames) - 1 and missing_frames[j + 1] == missing_frames[
                j] + 1 and counter % max_frames_per_job != max_frames_per_job - 1:
                j += 1
                counter += 1

            consolidated_frames.append((missing_frames[i], missing_frames[j] + 1))
            i = j + 1
            counter = 0

    else:
        for frame in missing_frames:
            consolidated_frames.append((frame, frame + 1))

    # clear existing jobs from multiparm
    jobs_multiparm = node.parm('envyJobs')
    jobs_multiparm.set(0)

    # make new jobs IF READ FROM DESCRIPTIVE FILE IMPLEMENT HERE
    for i, frame_range in enumerate(consolidated_frames):
        start_frame, end_frame = frame_range
        job_index = i + 1
        job = jobs_multiparm.insertMultiParmInstance(i)

        # set button to press
        node.parm(f'targetButton{job_index}').set(button_to_press_parm.rawValue())

        # create parameter edits parms
        parameter_edits_multiparm = node.parm(f'parameterEdits{job_index}')
        parameter_edits_multiparm.insertMultiParmInstance(0)
        parameter_edits_multiparm.insertMultiParmInstance(1)

        # set start frame
        node.parm(f'parm{job_index}_1').set(start_frame_parm.rawValue())
        node.parm(f'value{job_index}_1').set(str(start_frame))

        # set end frame
        node.parm(f'parm{job_index}_2').set(end_frame_parm.rawValue())
        node.parm(f'value{job_index}_2').set(str(end_frame))