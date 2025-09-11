import cv2
import sdl2
import sdl2.ext
import sys

# Try Pi-only imports
try:
    from picamera2 import Picamera2
    from libcamera import Transform
    import RPi.GPIO as GPIO
    ON_PI = True
except ImportError:
    ON_PI = False

# ---------------- Camera Abstraction ----------------
class CameraBase:
    def read(self):
        raise NotImplementedError
    def release(self):
        pass
    def get_frame_size(self):
        raise NotImplementedError

class MacCamera(CameraBase):
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")
    def read(self):
        return self.cap.read()
    def release(self):
        self.cap.release()
    def get_frame_size(self):
        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return w, h

class PiCamera(CameraBase):
    def __init__(self):
        self.picam2 = Picamera2()
        self.picam2.configure(
            self.picam2.create_preview_configuration(
                main={"format": "BGR888", "size": (640, 640)}
            )
        )
        transform=Transform(vflip=1)
        self.picam2.start()

    def read(self):
        frame = self.picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return True, frame

    def release(self):
        self.picam2.stop()

    def get_frame_size(self):
        frame = self.picam2.capture_array()
        h, w = frame.shape[:2]
        return w, h

# ---------------- PWM Setup ----------------
if ON_PI:
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # H-bridge pins: forward/backward for each axis
    PINS = {
        "X_FWD": 17,
        "X_BWD": 27,
        "Y_FWD": 13,
        "Y_BWD": 5,
    }

    for pin in PINS.values():
        GPIO.setup(pin, GPIO.OUT)

    pwm_x_fwd = GPIO.PWM(PINS["X_FWD"], 1000)
    pwm_x_bwd = GPIO.PWM(PINS["X_BWD"], 1000)
    pwm_y_fwd = GPIO.PWM(PINS["Y_FWD"], 1000)
    pwm_y_bwd = GPIO.PWM(PINS["Y_BWD"], 1000)

    for pwm in [pwm_x_fwd, pwm_x_bwd, pwm_y_fwd, pwm_y_bwd]:
        pwm.start(0)

MAX_PWM = 60.0  # % duty cycle cap

# Store last duty values for logging
last_state = {"x_axis": 0, "y_axis": 0, "x_duty": 0, "y_duty": 0}

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

# ---------------- Controller Setup ----------------
sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK)
if sdl2.SDL_NumJoysticks() < 1:
    print("No controller detected!")
    sys.exit()
joystick = sdl2.SDL_JoystickOpen(0)
print("Connected:", sdl2.SDL_JoystickName(joystick).decode())

# ---------------- Select Camera ----------------
camera = PiCamera() if ON_PI else MacCamera()
frame_width, frame_height = camera.get_frame_size()

# ---------------- Drawing State ----------------
cursor_x, cursor_y = frame_width // 2, frame_height // 2
drawing = False
color = (0, 0, 255)
radius = 5
overlay_points = []

# Controller mappings
JHAT_UP, JHAT_DOWN, JHAT_LEFT, JHAT_RIGHT, JHAT_CTR, BTN_DRAW = 1, 4, 8, 2, 0, 3
pad_state = {JHAT_UP: False, JHAT_DOWN: False, JHAT_LEFT: False, JHAT_RIGHT: False}
MOVE_SPEED = 5

# ---------------- Event Polling ----------------
def poll_controller():
    global drawing, cursor_x, cursor_y
    event = sdl2.SDL_Event()
    while sdl2.SDL_PollEvent(event):
        # Movement via D-pad (JHAT)
        if event.type == sdl2.SDL_JOYHATMOTION:
            if event.jhat.value == JHAT_CTR:
                for JHAT in pad_state:
                    pad_state[JHAT] = False
            elif event.jhat.value in pad_state:
                pad_state[event.jhat.value] = True
        elif event.type == sdl2.SDL_JOYBUTTONDOWN:
            if event.jbutton.button == BTN_DRAW:
                drawing = True
        elif event.type == sdl2.SDL_JOYBUTTONUP:
            if event.jbutton.button == BTN_DRAW:
                drawing = False
        elif event.type == sdl2.SDL_JOYAXISMOTION:
            # Handle axis motion
            if event.jaxis.axis == 0:  # X axis
                x_axis = event.jaxis.value
                set_magnetic_field(x_axis, last_state["y_axis"])
            elif event.jaxis.axis == 1:  # Y axis
                y_axis = event.jaxis.value
                set_magnetic_field(last_state["x_axis"], y_axis)
            log_state()

def update_cursor_position():
    global cursor_x, cursor_y
    if pad_state[JHAT_UP]:
        cursor_y -= MOVE_SPEED
    if pad_state[JHAT_DOWN]:
        cursor_y += MOVE_SPEED
    if pad_state[JHAT_LEFT]:
        cursor_x -= MOVE_SPEED
    if pad_state[JHAT_RIGHT]:
        cursor_x += MOVE_SPEED

    cursor_x = max(0, min(frame_width - 1, cursor_x))
    cursor_y = max(0, min(frame_height - 1, cursor_y))

# ---------------- Main Loop ----------------
try:
    while True:
        ret, frame = camera.read()
        if not ret:
            break

        poll_controller()
        update_cursor_position()

        if drawing:
            overlay_points.append((cursor_x, cursor_y))

        for px, py in overlay_points:
            cv2.circle(frame, (px, py), radius, color, -1)

        cv2.circle(frame, (cursor_x, cursor_y), radius+2, (0, 255, 0), 1)

        cv2.imshow("Camera + Drawing + Magnetic Control", frame)
        if cv2.waitKey(10) & 0xFF == 27:  # ESC
            break
finally:
    camera.release()
    if ON_PI:
        for pwm in [pwm_x_fwd, pwm_x_bwd, pwm_y_fwd, pwm_y_bwd]:
            pwm.stop()
        GPIO.cleanup()
    cv2.destroyAllWindows()
    print()  # move cursor to next line after logging