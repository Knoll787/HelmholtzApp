from gpiozero import PWMOutputDevice, OutputDevice, Device
import numpy as np

class Coil:
    def __init__(self, dir1, pwm1, dir2, pwm2):
        self.mode = "Helmholtz"
        self.dir1 = OutputDevice(dir1)
        self.pwm1 = PWMOutputDevice(pwm1)
        self.dir2 = OutputDevice(dir2)
        self.pwm2 = PWMOutputDevice(pwm2)
        self.frequency = 1000 # Hz

def set_coil(coils, pwm):
    if pwm >= 0.0:
        direction = "CW" # Clockwise
    else:
        direction = "ACW" # Anti-Clockwise
    power = abs(pwm/100)

    if mode == "Helmholtz":
        if direction == "CW":
            coils.dir1.on()
            coils.dir2.off()
        else:
            coils.dir1.off()
            coils.dir2.off()
        coils.pwm1.value= power
        coils.pwm2.value = power
    elif mode == "Maxwell":
        if direction == "CW":
            coils.dir1.on()
            coils.dir2.off()
        else:
            coils.dir1.off()
            coils.dir2.on()
        coils.pwm1.value= power
        coils.pwm2.value = power
    
    def set_mode(mode):
        self.mode = mode