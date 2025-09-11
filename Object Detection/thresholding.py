import cv2
import sdl2
import sdl2.ext
import sys

# try pi-only imports
try:
    from picamera2 import picamera2
    from libcamera import transform
    import rpi.gpio as gpio
    on_pi = true
except importerror:
    on_pi = false

# ---------------- camera abstraction ----------------
class camerabase:
    def read(self):
        raise notimplementederror
    def release(self):
        pass
    def get_frame_size(self):
        raise notimplementederror

class maccamera(camerabase):
    def __init__(self):
        self.cap = cv2.videocapture(0)
        if not self.cap.isopened():
            raise runtimeerror("could not open camera")
    def read(self):
        return self.cap.read()
    def release(self):
        self.cap.release()
    def get_frame_size(self):
        w = int(self.cap.get(cv2.cap_prop_frame_width))
        h = int(self.cap.get(cv2.cap_prop_frame_height))
        return w, h

class picamera(camerabase):
    def __init__(self):
        self.picam2 = picamera2()
        self.picam2.configure(
            self.picam2.create_preview_configuration(
                main={"format": "bgr888", "size": (640, 640)}
            )
        )
        transform=transform(vflip=1)
        self.picam2.start()

    def read(self):
        frame = self.picam2.capture_array()
        frame = cv2.cvtcolor(frame, cv2.color_rgb2bgr)
        return true, frame

    def release(self):
        self.picam2.stop()

    def get_frame_size(self):
        frame = self.picam2.capture_array()
        h, w = frame.shape[:2]
        return w, h

# ---------------- pwm setup ----------------
if on_pi:
    gpio.setmode(gpio.bcm)
    gpio.setwarnings(false)

    # h-bridge pins: forward/backward for each axis
    pins = {
        "x_fwd": 17,
        "x_bwd": 27,
        "y_fwd": 13,
        "y_bwd": 5,
    }

    for pin in pins.values():
        gpio.setup(pin, gpio.out)

    pwm_x_fwd = gpio.pwm(pins["x_fwd"], 1000)
    pwm_x_bwd = gpio.pwm(pins["x_bwd"], 1000)
    pwm_y_fwd = gpio.pwm(pins["y_fwd"], 1000)
    pwm_y_bwd = gpio.pwm(pins["y_bwd"], 1000)

    for pwm in [pwm_x_fwd, pwm_x_bwd, pwm_y_fwd, pwm_y_bwd]:
        pwm.start(0)

max_pwm = 60.0  # % duty cycle cap

# store last duty values for logging
last_state = {"x_axis": 0, "y_axis": 0, "x_duty": 0, "y_duty": 0}

def set_magnetic_field(x_val, y_val):
    """update pwm duty cycles based on joystick axes [-32768..32767]."""
    global last_state
    if not on_pi:
        return

    def scale(val):
        return max(-max_pwm, min(max_pwm, (val / 32767.0) * max_pwm))

    duty_x = scale(x_val)
    duty_y = scale(y_val)

    # x axis control
    if duty_x > 0:
        pwm_x_fwd.changedutycycle(duty_x)
        pwm_x_bwd.changedutycycle(0)
    elif duty_x < 0:
        pwm_x_fwd.changedutycycle(0)
        pwm_x_bwd.changedutycycle(abs(duty_x))
    else:
        pwm_x_fwd.changedutycycle(0)
        pwm_x_bwd.changedutycycle(0)

    # y axis control
    if duty_y > 0:
        pwm_y_fwd.changedutycycle(duty_y)
        pwm_y_bwd.changedutycycle(0)
    elif duty_y < 0:
        pwm_y_fwd.changedutycycle(0)
        pwm_y_bwd.changedutycycle(abs(duty_y))
    else:
        pwm_y_fwd.changedutycycle(0)
        pwm_y_bwd.changedutycycle(0)

    # save state for logging
    last_state = {
        "x_axis": x_val,
        "y_axis": y_val,
        "x_duty": duty_x,
        "y_duty": duty_y,
    }

def log_state():
    """print joystick + pwm state in one updating line."""
    print(
        f"joystick: x={last_state['x_axis']:6d}, y={last_state['y_axis']:6d} | "
        f"duty: x={last_state['x_duty']:6.2f}%, y={last_state['y_duty']:6.2f}%",
        end="\r",
        flush=true
    )

# ---------------- controller setup ----------------
sdl2.sdl_init(sdl2.sdl_init_joystick)
if sdl2.sdl_numjoysticks() < 1:
    print("no controller detected!")
    sys.exit()
joystick = sdl2.sdl_joystickopen(0)
print("connected:", sdl2.sdl_joystickname(joystick).decode())

# ---------------- select camera ----------------
camera = picamera() if on_pi else maccamera()
frame_width, frame_height = camera.get_frame_size()

# ---------------- drawing state ----------------
cursor_x, cursor_y = frame_width // 2, frame_height // 2
drawing = false
color = (0, 0, 255)
radius = 5
overlay_points = []

# controller mappings
jhat_up, jhat_down, jhat_left, jhat_right, jhat_ctr, btn_draw = 1, 4, 8, 2, 0, 3
pad_state = {jhat_up: false, jhat_down: false, jhat_left: false, jhat_right: false}
move_speed = 5

# ---------------- event polling ----------------
def poll_controller():
    global drawing, cursor_x, cursor_y
    event = sdl2.sdl_event()
    while sdl2.sdl_pollevent(event):
        # movement via d-pad (jhat)
        if event.type == sdl2.sdl_joyhatmotion:
            if event.jhat.value == jhat_ctr:
                for jhat in pad_state:
                    pad_state[jhat] = false
            elif event.jhat.value in pad_state:
                pad_state[event.jhat.value] = true
        elif event.type == sdl2.sdl_joybuttondown:
            if event.jbutton.button == btn_draw:
                drawing = true
        elif event.type == sdl2.sdl_joybuttonup:
            if event.jbutton.button == btn_draw:
                drawing = false
        elif event.type == sdl2.sdl_joyaxismotion:
            # handle axis motion
            if event.jaxis.axis == 0:  # x axis
                x_axis = event.jaxis.value
                set_magnetic_field(x_axis, last_state["y_axis"])
            elif event.jaxis.axis == 1:  # y axis
                y_axis = event.jaxis.value
                set_magnetic_field(last_state["x_axis"], y_axis)
            log_state()

def update_cursor_position():
    global cursor_x, cursor_y
    if pad_state[jhat_up]:
        cursor_y -= move_speed
    if pad_state[jhat_down]:
        cursor_y += move_speed
    if pad_state[jhat_left]:
        cursor_x -= move_speed
    if pad_state[jhat_right]:
        cursor_x += move_speed

    cursor_x = max(0, min(frame_width - 1, cursor_x))
    cursor_y = max(0, min(frame_height - 1, cursor_y))

# ---------------- main loop ----------------
try:
    while true:
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

        cv2.imshow("camera + drawing + magnetic control", frame)
        if cv2.waitkey(10) & 0xff == 27:  # esc
            break
finally:
    camera.release()
    if on_pi:
        for pwm in [pwm_x_fwd, pwm_x_bwd, pwm_y_fwd, pwm_y_bwd]:
            pwm.stop()
        gpio.cleanup()
    cv2.destroyallwindows()
    print()  # move cursor to next line after logging