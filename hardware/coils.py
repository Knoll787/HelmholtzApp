import platform
from gpiozero import PWMOutputDevice, OutputDevice, Device
from gpiozero.pins.mock import MockFactory, MockPin, MockPWMPin
import numpy as np

class Coils:
    def __init__(self, use_mock=None):
        # Assign MockPWMPin to all PWM pins
        factory = MockFactory()
        Device.pin_factory = factory
        


        # PWM_PINS[0] -> Coil 1 - Z Coil
        # PWM_PINS[1] -> Coil 2 - Z Coil
        # PWM_PINS[2] -> Coil 3 - Y Coil
        # PWM_PINS[3] -> Coil 4 - Y Coil
        # PWM_PINS[4] -> Coil 5 - X Coil
        # PWM_PINS[5] -> Coil 6 - X Coil
        self.PWM_PINS = [12, 20, 5, 13, 17, 27]
        for pin in self.PWM_PINS:
            factory.pin(pin, pin_class=MockPWMPin)


        # PIN_DIR[0] -> Coil 1 - Z Coil
        # PIN_DIR[1] -> Coil 2 - Z Coil
        # PIN_DIR[2] -> Coil 3 - Y Coil
        # PIN_DIR[3] -> Coil 4 - Y Coil
        # PIN_DIR[4] -> Coil 5 - X Coil
        # PIN_DIR[5] -> Coil 6 - X Coil
        self.PIN_DIR = [16, 21, 6, 19, 22, 23]

        PWM_FREQUENCY = 1000  # Hz
        #self.PWM = [PWMOutputDevice(pin, frequency=PWM_FREQUENCY) for pin in self.PWM_PINS]
        self.DIR = [OutputDevice(pin) for pin in self.PIN_DIR]

        self.M1 = np.array([0.1047, 0.1111, 0.1500, 0.1579, 0.2195, 0.2250])
        self.M1 = np.diag(self.M1)
        self.b1 = np.array([1, 1, 1, 1, 1, 1])

        self.M2 = np.array([0.1047, 0.1111, 0.1500, 0.1579, 0.2195, 0.2250])
        self.M2 = np.diag(self.M2)
        self.b2 = np.array([0.1489, 0.2567, -0.1000, -0.1667, 0.0000, -0.0556])
        
        self.M3 = self.M2 @ self.M1
        self.b3 = self.M2 @ self.b1 + self.b2

    def pwm_to_current(self, PWM):
        I = self.M1 @ PWM + self.b1
        return I # Current [A]

    def current_to_field(self, I):
        B = self.M2 @ I + self.b2
        return B # Field Strength [mT]

    def pwm_to_field(self, PWM):
        B = self.M3 @ PWM + self.b3
        return B # Field Strength [mT]

    def field_to_current(self, B):
        I = np.linalg.inv(self.M2) @ (B - self.b2)
        return I # Current [A]


    def current_to_pwm(self, I):
        PWM = np.linalg.inv(self.M1) @ (I - self.b1)
        return PWM # Duty Cycle [%]

    def field_to_pwm(self, B):
        PWM = np.linalg.inv(self.M3) @ (B - self.b3)
        return PWM # Duty Cycle [%]
        

if __name__ == '__main__':
    coils = Coils()
    PWM = [10, 50, 20, 80, 30, 100]
    I = coils.pwm_to_current(np.array(PWM))
    B = coils.current_to_field(np.array(I))

    print(coils.M2)



