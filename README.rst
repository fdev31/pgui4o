##################################
OctoPrint UI for touch LCD screens
##################################

Attempt to make the printer LCD controller useless if you have a Raspberry Pi

Optimized for 480x320 screens

Look at the `quick demo`__!

__ https://youtu.be/ve8TRxibCCY


Quickstart
##########

- Generate an OctoPrint API key from the settings menu & save it under `API_KEY.txt`

- Edit `run` script, uncomment "export" lines after changing to your own setup
    - edit PRINT_PORT and PRINTER_SPEED
    - if not running on the raspberry PI, edit OCTOPRINT_HOST

- start using `./run`

Shortcuts
=========

The following shortcuts are available

- **Q** to quit
- **F** to toggle fullscreen
- **+** and **-** to change the font size


Roadmap
#######

Look at the `TODO list`__

__ https://github.com/fdev31/pgui4o/blob/master/bugs.rst