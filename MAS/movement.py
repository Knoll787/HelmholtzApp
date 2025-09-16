import sdl2
import sys
import RPi.GPIO as GPIO
import time


class Gamepad:
    def __init__(self):
        sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK)
        if sdl2.SDL_NumJoysticks() < 1:
            print("No controller detected!")
            sys.exit()
        joystick = sdl2.SDL_JoystickOpen(0)
        print("Connected:", sdl2.SDL_JoystickName(joystick).decode())
        
        # JHAT Button Mappings
        self.JHAT_UP = 1
        self.JHAT_DOWN = 4
        self.JHAT_LEFT = 8
        self.JHAT_RIGHT = 2
        self.JHAT_CTR = 0

        # Button Mappings
        self.BTN_DRAW = 3

        # H-bridge pins: forward/backward for each axis
        self.PINS = {
            "X_FWD": 17,
            "X_BWD": 27,
            "Y_FWD": 13,
            "Y_BWD": 5,
        }

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for pin in self.PINS.values():
            GPIO.setup(pin, GPIO.OUT)

        self.pwm_x_fwd = GPIO.PWM(self.PINS["X_FWD"], 1000)
        self.pwm_x_bwd = GPIO.PWM(self.PINS["X_BWD"], 1000)
        self.pwm_y_fwd = GPIO.PWM(self.PINS["Y_FWD"], 1000)
        self.pwm_y_bwd = GPIO.PWM(self.PINS["Y_BWD"], 1000)

        for pwm in [self.pwm_x_fwd, self.pwm_x_bwd, self.pwm_y_fwd, self.pwm_y_bwd]:
            pwm.start(0)

        self.MAX_PWM = 60.0  # % duty cycle cap

        # Store last duty values for logging
        self.last_state = {"x_axis": 0, "y_axis": 0, "x_duty": 0, "y_duty": 0}
            
            
        # Other parameters
        self.MOVE_SPEED = 5
        self.pad_state = {self.JHAT_UP: False, 
                          self.JHAT_DOWN: False, 
                          self.JHAT_LEFT: False, 
                          self.JHAT_RIGHT: False
                         }
    
    def poll_controller(self):
        #global drawing, cursor_x, cursor_y
        event = sdl2.SDL_Event()
        while sdl2.SDL_PollEvent(event):
            # Movement via D-pad (JHAT)
            if event.type == sdl2.SDL_JOYHATMOTION:
                if event.jhat.value == self.JHAT_CTR:
                    for JHAT in self.pad_state:
                        self.pad_state[JHAT] = False
                elif event.jhat.value in self.pad_state:
                    self.pad_state[event.jhat.value] = True
            elif event.type == sdl2.SDL_JOYBUTTONDOWN:
                if event.jbutton.button == self.BTN_DRAW:
                    drawing = True
            elif event.type == sdl2.SDL_JOYBUTTONUP:
                if event.jbutton.button == self.BTN_DRAW:
                    drawing = False
            elif event.type == sdl2.SDL_JOYAXISMOTION:
                # Handle axis motion
                if event.jaxis.axis == 0:  # X axis
                    x_axis = event.jaxis.value
                    self.set_magnetic_field(x_axis, self.last_state["y_axis"])
                elif event.jaxis.axis == 1:  # Y axis
                    y_axis = event.jaxis.value
                    self.set_magnetic_field(self.last_state["x_axis"], y_axis)
                self.log_state()

    def scale(self, val):
        return max(-self.MAX_PWM, min(self.MAX_PWM, (val / 32767.0) * self.MAX_PWM))

    def set_magnetic_field(self, x_val, y_val):
        duty_x = self.scale(x_val)
        duty_y = self.scale(y_val)

        # X axis control
        if duty_x > 0:
            self.pwm_x_fwd.ChangeDutyCycle(duty_x)
            self.pwm_x_bwd.ChangeDutyCycle(0)
        elif duty_x < 0:
            self.pwm_x_fwd.ChangeDutyCycle(0)
            self.pwm_x_bwd.ChangeDutyCycle(abs(duty_x))
        else:
            self.pwm_x_fwd.ChangeDutyCycle(0)
            self.pwm_x_bwd.ChangeDutyCycle(0)

        # Y axis control
        if duty_y > 0:
            self.pwm_y_fwd.ChangeDutyCycle(duty_y)
            self.pwm_y_bwd.ChangeDutyCycle(0)
        elif duty_y < 0:
            self.pwm_y_fwd.ChangeDutyCycle(0)
            self.pwm_y_bwd.ChangeDutyCycle(abs(duty_y))
        else:
            self.pwm_y_fwd.ChangeDutyCycle(0)
            self.pwm_y_bwd.ChangeDutyCycle(0)

        # Save state for logging
        self.last_state = {
            "x_axis": x_val,
            "y_axis": y_val,
            "x_duty": duty_x,
            "y_duty": duty_y,
        }

    def log_state(self):
        """Print joystick + PWM state in one updating line."""
        print(
            f"Joystick: X={self.last_state['x_axis']:6d}, Y={self.last_state['y_axis']:6d} | "
            f"Duty: X={self.last_state['x_duty']:6.2f}%, Y={self.last_state['y_duty']:6.2f}%",
            end="\r",
            flush=True
        )
        
    def cleanup(self):
        for pwm in [self.pwm_x_fwd, self.pwm_x_bwd, self.pwm_y_fwd, self.pwm_y_bwd]:
            pwm.stop()
        GPIO.cleanup()
        