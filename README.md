## ENVY

Envy is a render manager with native Maya and Houdini support. Envy was built and designed for the Gnomon campus and that use case has influenced the design a great deal. As Envy was built for Gnomon students this readme will assume you are one.

## Features
- First class maya support: via the envy plugin
- First class Houdini support: via custom built HDAs
- User customization: each envy user is able to completely customize their instance's functionality. 
- Plugin support: for users to support any softwares in the future.
- Render node failover: If a render node is signed out the scheduler will simply reallocate the work to another node.
- Server failover: If the machine running the Envy server is signed out the remaining nodes will elect a new server.
- Management GUI: To allow users to graphically manage their work items.
- Automatic signout: To allow Gnomon students to take as many render nodes as needed without worrying about signing out of them in the morning.


## Installation
Installation is very simple!
1. Navigate to `\\titansrv\studentShare\__ENVY__\`
2. Copy the `envy` folder to your Z:/ drive
3. It's VERY IMPORTANT that the envy folder is at the root of your zdrive it should look like `Z:/envy`


## Usage
Using envy is also very simple 


## Requirements
Envy was built for the Gnomon campus and such has no gaurentee to work in other environments without some customization. Here are the major requirements:
- Some sort of network attached storage drive/partition which is unique to each user
- Some sort of network attached storage which all users have access to
- User's machines must be running Windows
- At least Python 3.10 on User's machines
- All User machines must be on the same LAN


## Resources
I created a discord servers for users to get in touch with me and report bugs. Feel free to [join](https://discord.gg/r259susGAS)!
