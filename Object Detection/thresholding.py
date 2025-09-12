import cv2
from picamera2 import Picamera2
from libcamera import Transform

# ---------------- Camera Abstraction ----------------
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

# ---------------- Magnet Tracking ----------------
def track_magnet(frame, min_area=500):
    """
    Detect the magnet and return its centroid + mask.
    Rejects blobs smaller than min_area.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Threshold for dark/black regions
    lower_black = (0, 0, 0)
    upper_black = (180, 255, 98)
    mask = cv2.inRange(hsv, lower_black, upper_black)

    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, mask

    # Filter contours by area
    contours = [c for c in contours if cv2.contourArea(c) >= min_area]
    if not contours:
        return None, mask

    # Largest valid contour = magnet
    c = max(contours, key=cv2.contourArea)
    M = cv2.moments(c)
    if M["m00"] == 0:
        return None, mask
    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])
    return (cx, cy), mask

# ---------------- Select Camera ----------------
camera = PiCamera()
frame_width, frame_height = camera.get_frame_size()

# ---------------- Main Loop ----------------
try:
    while True:
        ret, frame = camera.read()
        if not ret:
            break

        # Track magnet
        (mx, my), mask = track_magnet(frame, min_area=200)

        if (mx, my) is not None:
            cv2.circle(frame, (mx, my), 8, (255, 0, 0), 2)
            cv2.putText(frame, f"Magnet: ({mx},{my})", (mx+10, my),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 1)

        # Show both original frame and threshold mask
        cv2.imshow("Magnet Tracking", frame)
        cv2.imshow("Threshold Mask", mask)

        if cv2.waitKey(10) & 0xFF == 27:  # ESC
            break
finally:
    camera.release()
    cv2.destroyAllWindows()
    print()
