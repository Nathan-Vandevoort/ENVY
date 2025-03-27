https://github.com/user-attachments/assets/5e16fb8d-9d99-48ee-9af9-09e8594802d3

Envy is a render manager designed to help students with rendering and caching. It supports all render engines Gnomon supports as well as caching in Houdini. The design, features, and limitations of Envy are tailored specifically to the needs of the Gnomon campus. Because I created Envy for Gnomon students, this document will assume you are one.

## Table Of Contents
- [Features](#Features)
- [Installation](#Installation)
- [Requirements](#Requirements)
- [Resources](#Resources)
- [How-To](#How-To)
  - [Basics](#Basics)  
  - [Maya](#Maya)
  - [Houdini](#Houdini)
- [Customization](#Customization)
- [FAQ](#FAQ)
- [Glossary](#Glossary)


## Features
- **First class Maya support:** via the Envy plugin
- **Tiled rendering support in Maya:** via the Envy plugin
- **First class Houdini support:** via custom built HDAs
- **User customization:** each Envy user is able to completely customize their instance's functionality. 
- **Plugin support:** for users to support any softwares in the future.
- **Render node failover:** If a render node is signed out the scheduler will simply reallocate the work to another node.
- **Server failover:** If the machine running the Envy server is signed out the remaining nodes will elect a new server.
- **Management GUI:** For users to graphically manage their work items.
- **Automatic signout:** Allows Gnomon students to take as many render nodes as needed without worrying about signing out of them in the morning.
- **An update system:** Allows development while students use Envy.


## Installation
1. Navigate to `\\titansrv\studentShare\__ENVY__\`
2. Copy the `envy` folder to your Z:/ drive
3. It's **VERY IMPORTANT** that the Envy folder is at the root of your zdrive. It should look like `Z:/envy`


## Requirements
I built Envy for the Gnomon campus and may require customization before it works elsewhere.
- A network-attached storage drive/partition which is unique to each user
- A network-attached storage which all users have access to
- User machines must be running Windows
- At least Python 3.10 on user machines
- All user machines must be on the same LAN


## Resources
I created a discord servers for users to get in touch with me and report bugs. Feel free to [join](https://discord.gg/r259susGAS)!


## How-To
Using Envy is also very simple. The following section will be split in usage for Maya and Houdini feel free to skip to which ever section you require.

### Basics
Your `Z:/envy` folder should look kind of like this:

![envy_layout](https://github.com/user-attachments/assets/def6542b-82ef-484f-aa61-b51399753f53)

The `Launch_Envy.py` file is what you open on every computer you want to render on. Any computer running Envy will sign out at 8:30 am by default.

The `Launch_Console.pyw` file is what you open to monitor Envy and cancel jobs. Here's a walk through of the console:

![envy_console](https://github.com/user-attachments/assets/fddaacf3-8364-4e90-8f79-409ca07c30d9)


The Large window on the left is the viewport. Each one of the little blue balls represents a computer you have signed in. The top right window is your job viewer, you can see I have some jobs already created! In the bottom right window is your console, feel free to mess around with it! I'll talk more about the console in the [Customization](#Customization) section. If you ever want to cancel a job simply right click the job and mark it as finished.

***There are somethings to note about using Envy:** All of your dependencies (textures, references, caches, files, project, etc...) **MUST** be on a server `(Z:/ \\titansrv \\veloxsrv)`. If your job is not exporting, check your file paths.


### Maya

To setup the Maya plugin for Envy need to type `install_maya_plugin()` into the console and press enter. 

**Please Note:** This command will only install the Maya plugin if you have already opened maya this term. If you use a new version of Maya during the term you will need to type in `install_maya_plugin()` again.

The console should inform you that the Maya plugin was installed successfully. To use the plugin within maya open the plugin manager under `windows -> settings/preferences -> plugin manager` and then check `load` on the Envy plugin.

![maya plugin manager](https://github.com/user-attachments/assets/0ced8e6f-ce27-46c6-84de-7484288df233)

You should see an Envy menu appear at the top of Maya:

![envy dropdown](https://github.com/user-attachments/assets/cdb60104-68e3-4904-bdde-4786a2f0b1f8)

If you click that dropdown and select `Export to Envy` another UI window will appear and it will look like this:

![mayaUI-ezgif com-optimize](https://github.com/user-attachments/assets/5d959639-5b5d-4078-b62d-38069987d7be)

Right now you can see I have two cameras which are both inactive. To tell Envy to render this camera you simply click on the camera icon and it will turn blue. You can also click on the clock icon to adjust the frame range per camera to have Envy render your sequences for you. the `Start Frame` and `End Frame` parameters set themselves from your render settings but you can overwrite them within this UI. the `Batch Size` parameter is how many frames will be allocated to each computer, learn more about batch sizes and what they mean practically [here](#batch-size)! When you are ready to render click the render button! Envy will prompt you to save your scene, say yes or weird things may happen; or better yet increment and save your scene before exporting to Envy. If you get an error in your script editor at the bottom right follow these trouble shooting steps:

1. Is your project set? (Your project and maya file must be on the server)
2. Is your maya file / project on the server?
3. Check your file path editor under `windows -> general editors -> file path editor` and make sure that all of your paths look okay.
4. If it's still not working feel free to reach out in the discord server!


### Houdini

To use Envy in Houdini you need to load a couple of HDA's into your scene. The HDA's live under `envy/Plugins/eHoudini/HDAs` Inside of that folder you should find:

![HDA file layout](https://github.com/user-attachments/assets/2f66b48e-233b-4725-ac08-81fcf8c80d4e)

The NV_jobSubmitter HDA is the important one. The NVcache HDA is simply a normal file cache HDA with the job submitter wrapped inside of it (it also does some USD prep stuff). 
The job submitter is your bridge from houdini to Envy. It is capable of issuing: Render, Cache, and Simulation jobs. Here's how you use it!

#### Job Submitter Rendering

![jobProcessor_rendering](https://github.com/user-attachments/assets/e976795f-be20-482c-8b14-b99738e78b25)


To Render:

 1. Drag and drop your ROP node (will work for OUT context ROPs as well as solaris USD render ROP) into the `Render Node` parameter
 2. Click `Set From Node` (This pattern exists for all of the job types).
 3. Override the `Start Frame` and `End Frame` if needed
 4. Click `Write Job` and accept the save pop-up. To learn about the `Batch Size` parameter click [here](#batch-size).


#### Job Submitter Caching / Simulation

![jobProcessor_caching](https://github.com/user-attachments/assets/9ac02eff-92e3-4d86-91ee-dcf3f70ce158)


To Cache:
 
 1. Drag and drop your file-cache node into the `File Cache Node` parameter and click `Set From Node`.
 2. Edit your `Start Frame`, `End Frame`, `Substeps`, and `Version` parameters if needed.
 3. If you are caching a simulation check on the simulation checkbox. This will ensure Envy does not try to distribute the job (Envy does not support distributing simulations).
 4. If you have a non time dependant job then you can mess with the `Batch Size` [parameter](#batch-size).
 5. Click `Write Job` and accept the save scene popup.

#### Job Submitter Generic Job

![jobProcessor_generic](https://github.com/user-attachments/assets/e5920706-37fa-4f43-9c27-3bc868dd4e8e)


Generic Jobs are intended to be used for wedging. They allow you to have Envy press any arbitrary Houdini button and set any arbitrary parameters. To use Generic Jobs:

 1. drag and drop the button you want Envy to press in the `Button To Press` parameter field.
 2. Drag and drop the parameter(s) you want to set in the `Parameter` field.
 3. Input the desired value in the `Value` field.

**Note:** These Jobs don't give Envy some information such as your start frame and end frame and so they will appear as a single frame in your console. Generic jobs may also require more direct user management.


## Customization
Envy offers you a whole lot of customization if you don't mind writing a little bit of python. In your `envy/Plugins` folder you will see `Envy_Functions.py`, `Server_Functions.py`, and `Console_Functions.py`. Inside of these three python scripts is all the functionality of Envy. Feel free to poke around and look at how stuff works! At the top of each of those scripts I have some rules you have to follow for your functions to work there is also an example function for you to see how to write your own. If you want to extend Envy's functionality outside of just writing a few functions check out the `envy/Plugins/Example` folder. Inside of there I wrote an example plugin. If you follow the steps outlined there you can have envy run anything! I would also check out the on_start() function in `Envy_Functions.py` Envy will run that function on start-up so you can have envy display render messages or maybe do some house keeping tasks. Happy coding!

**Note:** If you receive a notification telling you that something is out of date and needs to be updated (you should probably say yes). But any customizations you made to that thing will be reset. So if you are customizing any of the scripts it's a good idea to save a copy of those files elsewhere and then paste the changes back in if needed.

![Plugin_Layout](https://github.com/user-attachments/assets/70c5c366-f992-47a0-8e7b-03fbc02eeea8)


## FAQ
 - Q: Will Envy do Skip Rendered Frames?
   - A: Envy will never re-allocate a finished frame. However, if you create a new job and tell Envy to render frames 1-100 Envy will render frames 1-100 regardless if some of those frames are already rendered.
 - Q: What happens if all my computers sign out but not all my frames are finished?
   - A: If you start up some more Envy instances they will pick back up where they left off.
 - Q: I'm not getting any frames from Envy!
   - A: Check your scene and project. If Envy hasnt marked those frames as `Done` then they aren't done maybe your render settings are too crazy? If you are getting frames that look weird, check your dependencies and makes sure all of them are on the server. Envy is just pressing the render button for you it's not doing anything fancy.
 - Q: I was messing around with my `Envy_Functions.py` script and I broke Envy!
   - A: No worries just pull the broken file again from the `\\titansrv`
 - Q: I'm marking jobs as finished but it's not working!
   - A: If Envy is not running somewhere you won't be able to mark jobs as finished.


## Glossary
### batch size
To put it simply the batch size is how many frames will Envy try to give each computer. You may want to increase this number if you have very fast renders (less then 2 minutes per frame). Under the hood Envy needs to launch whatever software you want to render in (maya, houdini, etc...) and that can take time. The batch size tells Envy how often should each computer restart that software. If it takes longer to open maya then it does to render your frame then you probably want to increase your batch size. The batchsize also tells Envy how many work items the scheduler can allocate. which is `(frame range // batch size)`.


For Example: if you have 100 frames to render and a batch size of 10 then 10 computers will be able to work on your job. This can be not optimal if you have 20 computers running envy as 10 of them wont have any work. 
In this case you may want to set a lower batchsize such as 5. If you dont want to worry about batch size just leave it at 1.

## Contributing
Create a virtual environment
```shell
python -m venv venv
```

activate the virtual environment
```shell
venv/Scripts/activate
```

to install dependencies 
```shell
pip install .
```