# Magnetic Actuation System
## Getting started
Getting started is straight forward. Simply power on the coils, then run the following commands:
```
cd Helmholtz/MAS/
python3 run_me.py
```
This will run a script that enables the demonstration of the core aspects of the project:
1. Coil Control: Manually adjust the PWM and direction of the current in each coil
2. Open Loop Control: Move a magnetic agent around the workspace using a joystick
3. Closed Loop Control: This allows for a region of interest to be defined by clicking on the screen. A path can then be drawn using the mouse and the magnetic agent will following along that path