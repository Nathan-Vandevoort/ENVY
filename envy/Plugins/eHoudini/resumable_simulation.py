import json, sys, os

def set_environment(hip, job):
    hou.putenv('JOB', job)
    hou.hipFile.load(hip)

def set_parameters(parameter_dict: dict) -> None:
    for parm in parameter_dict:
        # set the value of the parm
        targetParm = hou.parm(parm)
        value = parameter_dict[parm]
        targetParm.setExpression(str(value), language=hou.exprLanguage.Hscript)
        targetParm.pressButton()
        print(f'Set parameter: {parm} -> {value}', flush=True)

def press_target_button(target_button) -> None:
    parm = hou.parm(target_button)
    parm.pressButton()
    print(f'Pressed target button {target_button}')


def get_latest_sim_file(sim_dir: str, hipname: str, operator_string: str, job_id: int):
    try:
        sim_files = os.listdir(sim_dir)
    except OSError:
        return None

    sim_files_gathered = {}
    for sim_file in sim_files:
        name, ext = os.path.splitext(sim_file)
        name_split = name.split(".")

        try:
            sim_frame = int(float(name_split[-1]))
            start_frame = int(float(name_split[-2]))
            file_operator_string = name_split[-4]
            file_hipname = name_split[-5]
            file_job_id = int(name_split[-3])
        except ValueError:
            continue

        if file_hipname != hipname:
            continue

        if file_operator_string != operator_string:
            continue

        if file_job_id != job_id:
            continue

        sim_files_gathered[sim_frame + start_frame] = {
            'File': os.path.join(sim_dir, sim_file).replace('\\\\', '/').replace('\\', '/'),
            'Start_Frame': start_frame,
            'Sim_Frame': sim_frame
        }

    sim_files_sorted = list(sim_files_gathered)
    sim_files_sorted.sort()

    try:
        return_file = sim_files_gathered[sim_files_sorted[-1]]
    except IndexError:
        return_file = None

    return return_file

data_string = sys.argv[1]
data = json.loads(data_string.replace("'", '"'))

environment = data['Environment']
parameters = data['Parameters']
hip = environment['HIP']
job = environment['JOB']
version_dict = environment['Version']
substeps_dict = environment['Substeps']
target_button = environment['Target_Button']

tasks = data['Tasks']
task_list = list(tasks)
start_frame_dict = environment['Start_Frame']

start_frame_key = None
for key in start_frame_dict:
    start_frame_key = key
    start_frame_dict[key] = tasks[task_list[0]]

end_frame_dict = environment['End_Frame']

for key in end_frame_dict:
    start_frame_dict[key] = tasks[task_list[-1]]

set_environment(hip, job)  # load the hip file and set project

# resumable cache data
job_id = environment['Job_Id']
hip_name = hip.split('/').pop()
hip_name = hip_name.split('.')[0]

operator_string = environment['$OS']

dopnet_start_frame_parm = hou.parm(environment['Dopnet_Start_Frame_Parm'])

dopnet_node = dopnet_start_frame_parm.node()

sim_file_path_parm_path = environment['Checkpoint_File_Path'][0]
sim_file_schema = environment['Checkpoint_File_Path'][1]
sim_file_directory = os.path.dirname(sim_file_schema)

sim_file_data = get_latest_sim_file(sim_file_directory, hip_name, operator_string, job_id)

if sim_file_data is not None:
    sim_file = sim_file_data['File']
    new_start_frame = sim_file_data['Start_Frame'] + sim_file_data['Sim_Frame']

    print(f'$ENVY:NEWSTARTFRAME={int(new_start_frame) - int(tasks[task_list[0]])}', flush=True)  # to tell the ehoudini plugin that hey i'm starting on this frame because its my most recent sim file

    new_sim_file_path = sim_file_schema.replace('$STARTFRAMETOKEN', str(new_start_frame))  # replace the start frame token with the starting frame
    new_sim_file_path = new_sim_file_path.replace('$JOBID', str(job_id))

    #  update start frame dict
    start_frame_dict[start_frame_key] = new_start_frame

    #  set the dopnets initial state
    dopnet_initial_state_parm = environment['Dopnet_Initial_State_Parm']
    dopnet_initial_state_parm = hou.parm(dopnet_initial_state_parm)
    dopnet_initial_state_parm.set(sim_file)

    # set the dopnets start frame
    dopnet_start_frame_parm.set(int(new_start_frame))

else:
    new_sim_file_path = sim_file_schema.replace('$STARTFRAMETOKEN', str(start_frame_dict[start_frame_key]))
    new_sim_file_path = new_sim_file_path.replace('$JOBID', str(job_id))

# enable checkpointing on the dopnet
dopnet_node.parm('explicitcache').set(1)

# set the dopnets checkpoint file path
hou.parm(sim_file_path_parm_path).set(new_sim_file_path)

# set checkpoint trail length
hou.parm(environment['Checkpoint_Trail_Length'][0]).set(environment['Checkpoint_Trail_Length'][1])

# set checkpoint interval
hou.parm(environment['Checkpoint_Interval'][0]).set(environment['Checkpoint_Interval'][1])

set_parameters(start_frame_dict)
set_parameters(end_frame_dict)
set_parameters(version_dict)
set_parameters(substeps_dict)
set_parameters(parameters)
press_target_button(target_button)
hou.exit()
