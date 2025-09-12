import sdl2
import sys
import RPi.GIPO as GPIO

class Controller:
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
        
        # Other parameters
        self.MOVE_SPEED = 5
        pad_state = {JHAT_UP: False, JHAT_DOWN: False, JHAT_LEFT: False, JHAT_RIGHT: False}
    
def poll_controller():
    global drawing, cursor_x, cursor_y
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
                set_magnetic_field(last_state["x_axis"], y_axis)
            log_state()

def set_magnetic_field(x_val, y_val):
    """Update PWM duty cycles based on joystick axes [-32768..32767]."""
    global last_state
    if not ON_PI:
        return

    def scale(val):
        return max(-MAX_PWM, min(MAX_PWM, (val / 32767.0) * MAX_PWM))

    duty_x = scale(x_val)
    duty_y = scale(y_val)

    # X axis control
    if duty_x > 0:
        pwm_x_fwd.ChangeDutyCycle(duty_x)
        pwm_x_bwd.ChangeDutyCycle(0)
    elif duty_x < 0:
        pwm_x_fwd.ChangeDutyCycle(0)
        pwm_x_bwd.ChangeDutyCycle(abs(duty_x))
    else:
        pwm_x_fwd.ChangeDutyCycle(0)
        pwm_x_bwd.ChangeDutyCycle(0)

    # Y axis control
    if duty_y > 0:
        pwm_y_fwd.ChangeDutyCycle(duty_y)
        pwm_y_bwd.ChangeDutyCycle(0)
    elif duty_y < 0:
        pwm_y_fwd.ChangeDutyCycle(0)
        pwm_y_bwd.ChangeDutyCycle(abs(duty_y))
    else:
        pwm_y_fwd.ChangeDutyCycle(0)
        pwm_y_bwd.ChangeDutyCycle(0)

    # Save state for logging
    last_state = {
        "x_axis": x_val,
        "y_axis": y_val,
        "x_duty": duty_x,
        "y_duty": duty_y,
    }

def log_state():
    """Print joystick + PWM state in one updating line."""
    print(
        f"Joystick: X={last_state['x_axis']:6d}, Y={last_state['y_axis']:6d} | "
        f"Duty: X={last_state['x_duty']:6.2f}%, Y={last_state['y_duty']:6.2f}%",
        end="\r",
        flush=True
    )