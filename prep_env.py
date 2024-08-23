import os
import site
import sys
import importlib.util  # so I can dynamically import custom functions
import configparser

abs_file = os.path.abspath(__file__)
file_dir = os.path.dirname(abs_file)

config = configparser.ConfigParser()
config.read(os.path.join(file_dir, 'config.ini'))

ENVYPATH = config.get('DEFAULT', 'ENVYPATH')
os.environ['ENVYPATH'] = ENVYPATH

if ENVYPATH not in sys.path:
    sys.path.append(ENVYPATH)

try:
    calling_script_name = sys.modules['__main__'].__file__
except Exception as e:
    calling_script_name = ''
if 'launch_envy.py' in calling_script_name:

    modules = [
        'Envy_Functions',
        'Server_Functions'
    ]

    for module in modules:
        envy_functions_path = os.path.join(ENVYPATH, 'Plugins', module + '.py')
        spec = importlib.util.spec_from_file_location(module, envy_functions_path)
        module_object = importlib.util.module_from_spec(spec)
        sys.modules[module] = module_object
        spec.loader.exec_module(module_object)

if 'server.py' in calling_script_name:
    print('prepping server')

    modules = [
        'Envy_Functions',
        'Server_Functions'
    ]

    for module in modules:
        envy_functions_path = os.path.join(ENVYPATH, 'Plugins', module + '.py')
        spec = importlib.util.spec_from_file_location(module, envy_functions_path)
        module_object = importlib.util.module_from_spec(spec)
        sys.modules[module] = module_object
        spec.loader.exec_module(module_object)

if 'launch_console.py' in calling_script_name:
    print('prepping console')

    modules = [
        'Console_Functions',
        'Server_Functions'
    ]

    for module in modules:
        envy_functions_path = os.path.join(ENVYPATH, 'Plugins', module + '.py')
        spec = importlib.util.spec_from_file_location(module, envy_functions_path)
        module_object = importlib.util.module_from_spec(spec)
        sys.modules[module] = module_object
        spec.loader.exec_module(module_object)

bin_dir = file_dir + '/venv/Scripts/'
base = bin_dir[: -len("Scripts") - 1]  # strip away the bin part from the __file__, plus the path separator

# prepend bin to PATH (this file is inside the bin directory)
os.environ["PATH"] = os.pathsep.join([bin_dir, *os.environ.get("PATH", "").split(os.pathsep)])
os.environ["VIRTUAL_ENV"] = base  # virtual env is right above bin directory
os.environ["VIRTUAL_ENV_PROMPT"] = "" or os.path.basename(base)  # noqa: SIM222
# add the virtual environments libraries to the host python import mechanism
prev_length = len(sys.path)
for lib in "..\\Lib\\site-packages".split(os.pathsep):
    path = os.path.realpath(os.path.join(bin_dir, lib))
    site.addsitedir(path.decode("utf-8") if "" else path)
sys.path[:] = sys.path[prev_length:] + sys.path[0:prev_length]

sys.real_prefix = sys.prefix
sys.prefix = base