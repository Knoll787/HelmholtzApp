import cv2
import sdl2
import sdl2.ext
from picamera2 import Picamera2, Preview
from libcamera import Transform

# Init SDL2 for joystick
sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK)
if sdl2.SDL_NumJoysticks() < 1:
    print("No controller detected!")
    exit()
joystick = sdl2.SDL_JoystickOpen(0)
print("Connected:", sdl2.SDL_JoystickName(joystick).decode())

# Init PiCamera2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": "BGR888", "size": (480, 480)}))
transform=Transform(vflip=1) 
picam2.start()

# Cursor position
cursor_x, cursor_y = 320, 240
drawing = False
color = (0, 0, 255)
radius = 5

# Store drawn points persistently
overlay_points = []

# Button mappings for D-pad
BTN_UP = 11
BTN_DOWN = 12
BTN_LEFT = 13
BTN_RIGHT = 14
BTN_DRAW = 0  # A button

# Track which D-pad buttons are held down
pad_state = {BTN_UP: False, BTN_DOWN: False, BTN_LEFT: False, BTN_RIGHT: False}

# Movement speed in pixels/frame
MOVE_SPEED = 5


def poll_controller():
    """Check SDL2 events and update button states."""
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


def update_cursor_position(frame_width, frame_height):
    """Move the cursor based on D-pad state."""
    global cursor_x, cursor_y
    if pad_state[BTN_UP]:
        cursor_y -= MOVE_SPEED
    if pad_state[BTN_DOWN]:
        cursor_y += MOVE_SPEED
    if pad_state[BTN_LEFT]:
        cursor_x -= MOVE_SPEED
    if pad_state[BTN_RIGHT]:
        cursor_x += MOVE_SPEED

    # Keep cursor in frame bounds
    cursor_x = max(0, min(frame_width - 1, cursor_x))
    cursor_y = max(0, min(frame_height - 1, cursor_y))


while True:
    # Capture frame from PiCamera2
    frame = picam2.capture_array()
    frame_height, frame_width = frame.shape[:2]

    poll_controller()
    update_cursor_position(frame_width, frame_height)

    # Store point if drawing
    if drawing:
        overlay_points.append((cursor_x, cursor_y))

    # Draw stored points
    for px, py in overlay_points:
        cv2.circle(frame, (px, py), radius, color, -1)

    # Draw cursor
    cv2.circle(frame, (cursor_x, cursor_y), radius+2, (0, 255, 0), 1)

    cv2.imshow("Camera + Controller Drawing", frame)
    if cv2.waitKey(10) & 0xFF == 27:  # ESC to quit
        break

picam2.stop()
cv2.destroyAllWindows()
