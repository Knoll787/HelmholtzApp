import platform
from gpiozero import PWMOutputDevice, OutputDevice, Device
from gpiozero.pins.mock import MockFactory, MockPin, MockPWMPin
import numpy as np

# Assign MockPWMPin to all PWM pins
factory = MockFactory()
Device.pin_factory = factory

# PWM_PINS[0] -> Coil 1 - Z Coil
# PWM_PINS[1] -> Coil 2 - Z Coil
# PWM_PINS[2] -> Coil 3 - Y Coil
# PWM_PINS[3] -> Coil 4 - Y Coil
# PWM_PINS[4] -> Coil 5 - X Coil
# PWM_PINS[5] -> Coil 6 - X Coil
PWM_PINS = [12, 20, 5, 13, 17, 27]
for pin in PWM_PINS:
    factory.pin(pin, pin_class=MockPWMPin)


# PIN_DIR[0] -> Coil 1 - Z Coil
# PIN_DIR[1] -> Coil 2 - Z Coil
# PIN_DIR[2] -> Coil 3 - Y Coil
# PIN_DIR[3] -> Coil 4 - Y Coil
# PIN_DIR[4] -> Coil 5 - X Coil
# PIN_DIR[5] -> Coil 6 - X Coil
PIN_DIR = [16, 21, 6, 19, 22, 23]

PWM_FREQUENCY = 1000  # Hz
#self.PWM = [PWMOutputDevice(pin, frequency=PWM_FREQUENCY) for pin in self.PWM_PINS]
DIR = [OutputDevice(pin) for pin in PIN_DIR]

M1 = np.array([0.1047, 0.1111, 0.1500, 0.1579, 0.2195, 0.2250])
M1 = np.diag(M1)
b1 = np.array([1, 1, 1, 1, 1, 1])

M2 = np.array([0.1047, 0.1111, 0.1500, 0.1579, 0.2195, 0.2250])
M2 = np.diag(M2)
b2 = np.array([0.1489, 0.2567, -0.1000, -0.1667, 0.0000, -0.0556])

M3 = M2 @ M1
b3 = M2 @ b1 + b2

def pwm_to_current(PWM):
    I = M1 @ PWM + b1
    return I # Current [A]

def current_to_field(I):
    B = M2 @ I + b2
    return B # Field Strength [mT]

def pwm_to_field(PWM):
    B = M3 @ PWM + b3
    return B # Field Strength [mT]

def field_to_current(B):
    I = np.linalg.inv(M2) @ (B - b2)
    return I # Current [A]


def current_to_pwm(I):
    PWM = np.linalg.inv(M1) @ (I - b1)
    return PWM # Duty Cycle [%]

def field_to_pwm(B):
    PWM = np.linalg.inv(M3) @ (B - b3)
    return PWM # Duty Cycle [%]