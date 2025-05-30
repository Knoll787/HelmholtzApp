import platform
from gpiozero import PWMOutputDevice, OutputDevice, Device
from gpiozero.pins.mock import MockFactory, MockPin, MockPWMPin
import numpy as np

class Coils:
    def __init__(self, use_mock=None):
        # Assign MockPWMPin to all PWM pins
        factory = MockFactory()
        Device.pin_factory = factory
        self.PWM_PINS = [12, 20, 5, 13, 17, 27]
        for pin in self.PWM_PINS:
            factory.pin(pin, pin_class=MockPWMPin)


        #self.PIN_PWM = [12, 20, 5, 13, 17, 27]
        self.PIN_DIR = [16, 21, 6, 19, 22, 23]

        PWM_FREQUENCY = 1000  # Hz
        #self.PWM = [PWMOutputDevice(pin, frequency=PWM_FREQUENCY) for pin in self.PWM_PINS]
        self.DIR = [OutputDevice(pin) for pin in self.PIN_DIR]

    def pwm_to_current(self, PWM):
        M = np.array([0.1047, 0.1111, 0.1500, 0.1579, 0.2195, 0.2250])
        M = np.diag(M)
        b = np.array([1, 1, 1, 1, 1, 1])
        I = M @ PWM + b
        print(I)
        return I

    """
    def current_to_field(I):
        return B

    def pwm_to_field(PWM):
        return B

    def field_to_current(PWM):
        return I

    def current_to_pwm(I):
        return B

    def field_to_pwm(PWM):
        return B
    """
        

if __name__ == '__main__':
    coils = Coils()
    x = [10, 50, 20, 80, 30, 60]
    coils.pwm_to_current(np.array(x))
