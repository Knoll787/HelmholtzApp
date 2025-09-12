import cv2
import numpy as np
from picamera2 import Picamera2
from libcamera import Transform
import numpy as np

class CameraBase:
    def read(self):
        raise NotImplementedError
    def release(self):
        pass
    def get_frame_size(self):
        raise NotImplementedError

class PiCamera(CameraBase):
    def __init__(self):
        self.picam2 = Picamera2()
        self.picam2.configure(
            self.picam2.create_preview_configuration(
                main={"format": "BGR888", "size": (640, 640)}
            )
        )
        transform = Transform(vflip=1)
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
    
    
camera = PiCamera()
ret, first_frame = camera.read()
if not ret:
    raise RuntimeError("Could not read first frame from PiCamera")

try:
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        cv2.imshow("Error Tracking", frame)
        if cv2.waitKey(10) & 0xFF == 27:
            break
finally:
    camera.release()
    cv2.destroyAllWindows()
    print("Exited cleanly.")
