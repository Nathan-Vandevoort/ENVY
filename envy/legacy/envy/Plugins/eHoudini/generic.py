import json, sys

def set_environment(hip, job):
    hou.putenv('JOB', job)
    hou.hipFile.load(hip, suppress_save_prompt=True, ignore_load_warnings=True)

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
target_button = environment['Target_Button']

set_environment(hip, job)
set_parameters(parameters)
press_target_button(target_button)
hou.exit()