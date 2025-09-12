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

# ---------------- Select Camera ----------------
camera = PiCamera() if ON_PI else MacCamera()
frame_width, frame_height = camera.get_frame_size()

# ---------------- Event Polling ----------------
try:
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        cv2.imshow("Camera + Drawing + Magnetic Control", frame)
        if cv2.waitKey(10) & 0xFF == 27:  # ESC
            break
finally:
    camera.release()
    cv2.destroyAllWindows()
    print()  # move cursor to next line after logging