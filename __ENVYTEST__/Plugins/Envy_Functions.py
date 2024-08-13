import user_config, sys
sys.path.append(user_config.Config.REPOPATH)
from networkUtils import message as m
from networkUtils.purpose import Purpose
from envyLib.colors import Colors as c
from envyLib import envy_utils as eutils


def debug(envy) -> None:
    """
    a generic debug function feel free to change this to whatever you want it to do
    called from console with debug_envy()
    :param envy: reference to the envy instance calling the function
    :return: Void
    """
    print(f'{c.IMPORTANT}Debug{c.CLEAR}')


def fill_buffer(envy, buffer_name: str, data: any) -> None:
    """
    fills a buffer on envy given the buffers name and data to fill the buffer with
    :param envy: reference to the envy instance calling the function
    :param buffer_name: (str) name of buffer
    :param data: (any) data to fill buffer with
    :return: Void
    """
    setattr(envy, buffer_name, data)


def install_maya_plugin(envy) -> None:
    """
    installs the Maya plugin
    :param envy: reference to the envy instance calling the function
    """
    e_maya_path = '//titansrv/studentShare/nathanV/Envy_V2/ENVYTEST/Plugins/eMaya'
    user_maya_path = 'Z:/maya'

    """
    TODO: look for maya versions
    creates plugin folder if it does not exists
    check if there is the envy.py installed already, probably replace it so it could be updated all the time
    copy the envy.py file for each maya version in the user maya folder 
    """


def restart_envy(envy) -> None:
    import os
    """
    launches a new envy instance and shuts down the current one
    :param envy: reference to the envy instance calling the function
    :return: Void
    """
    #repopath = user_config.Config.REPOPATH
    os.startfile(f"launch_envy.py", cwd='//titansrv/studentShare/nathanV/Envy_V2/__ENVY__/')
    quit()

