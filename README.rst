##################################
OctoPrint UI for LCD touch screens
##################################

Attempt to make the printer LCD controller unnecessary if you have an Octopi__ setup

__ https://github.com/guysoft/OctoPi

Optimized for 480x320 screens, like the ones you can get on Aliexpress__

__ https://www.aliexpress.com/w/wholesale-320x480-raspberry.html

Watch the `short demo`__!

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
- click on the right "bar" on the UI to discover some features (depending on the chosen theme)


Roadmap
#######

Look at the `TODO list`__

__ https://github.com/fdev31/pgui4o/blob/master/tickets.rst

Developers / customizing
########################

Contributors are welcome, here are some reference commits as quick starts

Adding a new screen to the UI with new actions & attributes:

`be6d9ae3e30a23a63a9d857682707e4206b6ebdd <https://github.com/fdev31/pgui4o/commit/be6d9ae3e30a23a63a9d857682707e4206b6ebdd>`_
   
