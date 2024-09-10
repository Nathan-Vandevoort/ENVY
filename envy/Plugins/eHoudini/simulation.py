import json, sys

def set_environment(hip, job):
    hou.putenv('JOB', job)
    hou.hipFile.load(hip)

def set_parameters(parameter_dict: dict) -> None:
    for parm in parameter_dict:
        # set the value of the parm
        targetParm = hou.parm(parm)
        value = parameter_dict[parm]
        print(value)
        targetParm.setExpression(str(value), language=hou.exprLanguage.Hscript)
        targetParm.pressButton()
        print(f'Set parameter: {parm} -> {value}', flush=True)

def press_target_button(target_button) -> None:
    parm = hou.parm(target_button)
    parm.pressButton()
    print(f'Pressed target button {target_button}')


data_string = sys.argv[1]
data = json.loads(data_string.replace("'", '"'))
environment = data['Environment']
parameters = data['Parameters']
hip = environment['HIP']
job = environment['JOB']
tasks = data['Tasks']
start_frame_dict = environment['Start_Frame']
start_frame = start_frame_dict[list(start_frame_dict.keys())[0]]
end_frame_dict = environment['End_Frame']
end_frame = end_frame_dict[list(end_frame_dict.keys())[0]]
version_dict = environment['Version']
substeps_dict = environment['Substeps']
target_button = environment['Target_Button']

print(f'$ENVY:NEWSTARTFRAME={int(end_frame) - int(start_frame) - int(len(list(tasks)))}', flush=True)  # to tell the plugin to not mark the wrong tasks as complete

set_environment(hip, job)
set_parameters(start_frame_dict)
set_parameters(end_frame_dict)
set_parameters(version_dict)
set_parameters(substeps_dict)
set_parameters(parameters)
press_target_button(target_button)
hou.exit()