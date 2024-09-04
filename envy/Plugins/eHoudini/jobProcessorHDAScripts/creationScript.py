import os
import sys
myNode = kwargs['node']

#check to see if envy is installed on current computer
if( not os.path.isdir('Z:/envy/') ):
    hou.ui.displayMessage(f"Envy does not appear to be installed at the root of the Z drive\nThis Node WILL NOT work")
    exit()

directory = 'Z:/envy/utils'
if directory not in sys.path:
    sys.path.append('Z:/envy/utils')
import config_bridge as config


JOBPATH = os.path.join(config.Config.ENVYPATH, 'Jobs', 'Jobs')
myNode.parm('jobOutputPath').set(JOBPATH)