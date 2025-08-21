import cv2
import sdl2
import sdl2.ext

# Try importing PiCamera2 (works only on Pi)
try:
    from picamera2 import Picamera2
    from libcamera import Transform
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
                main={"format": "BGR888", "size": (480, 480)}
            )
        )
        self.picam2.start()
    def read(self):
        frame = self.picam2.capture_array()
        return True, frame
    def release(self):
        self.picam2.stop()
    def get_frame_size(self):
        frame = self.picam2.capture_array()
        h, w = frame.shape[:2]
        return w, h


# ---------------- Controller Setup ----------------
sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK)
if sdl2.SDL_NumJoysticks() < 1:
    print("No controller detected!")
    exit()
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
BTN_UP, BTN_DOWN, BTN_LEFT, BTN_RIGHT, BTN_DRAW = 11, 12, 13, 14, 0
pad_state = {BTN_UP: False, BTN_DOWN: False, BTN_LEFT: False, BTN_RIGHT: False}
MOVE_SPEED = 5


def poll_controller():
    global drawing
    event = sdl2.SDL_Event()
    while sdl2.SDL_PollEvent(event):
        if event.type == sdl2.SDL_JOYBUTTONDOWN:
            if event.jbutton.button in pad_state:
                pad_state[event.jbutton.button] = True
            elif event.jbutton.button == BTN_DRAW:
                drawing = True
        elif event.type == sdl2.SDL_JOYBUTTONUP:
            if event.jbutton.button in pad_state:
                pad_state[event.jbutton.button] = False
            elif event.jbutton.button == BTN_DRAW:
                drawing = False


def update_cursor_position():
    global cursor_x, cursor_y
    if pad_state[BTN_UP]:
        cursor_y -= MOVE_SPEED
    if pad_state[BTN_DOWN]:
        cursor_y += MOVE_SPEED
    if pad_state[BTN_LEFT]:
        cursor_x -= MOVE_SPEED
    if pad_state[BTN_RIGHT]:
        cursor_x += MOVE_SPEED

    # Keep inside bounds
    cursor_x = max(0, min(frame_width - 1, cursor_x))
    cursor_y = max(0, min(frame_height - 1, cursor_y))


# ---------------- Main Loop ----------------
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

    cv2.imshow("Camera + Controller Drawing", frame)
    if cv2.waitKey(10) & 0xFF == 27:
        break

camera.release()
cv2.destroyAllWindows()
