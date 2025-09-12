import cv2
import numpy as np
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

# ---------------- ROI Selection ----------------
roi_points = []
roi_mask = None

def mouse_callback(event, x, y, flags, param):
    global roi_points, roi_mask
    if event == cv2.EVENT_LBUTTONDOWN:
        roi_points.append((x, y))
        if len(roi_points) == 4:
            # Create polygon mask
            mask = np.zeros(param.shape[:2], dtype=np.uint8)
            cv2.fillPoly(mask, [np.array(roi_points, dtype=np.int32)], 255)
            roi_mask = mask
            print("ROI set. Press any key to continue.")

# ---------------- Magnet Tracking ----------------
def track_magnet(frame,
                 lower_black=(0, 0, 0),
                 upper_black=(180, 255, 95),
                 min_area=500,
                 hole_fill=True):
    """Detect magnet and return its centroid or None, plus mask."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower_black), np.array(upper_black))

    # Restrict to ROI
    global roi_mask
    if roi_mask is not None:
        mask = cv2.bitwise_and(mask, roi_mask)

    # Morphological cleanup
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)

    # Fill holes
    if hole_fill:
        im_inv = cv2.bitwise_not(mask)
        h, w = im_inv.shape[:2]
        im_floodfill = im_inv.copy()
        mask_ff = np.zeros((h + 2, w + 2), np.uint8)
        cv2.floodFill(im_floodfill, mask_ff, (0, 0), 255)
        im_floodfill_inv = cv2.bitwise_not(im_floodfill)
        mask = cv2.bitwise_or(mask, im_floodfill_inv)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) >= min_area]
    if not contours:
        return None, mask

    c = max(contours, key=cv2.contourArea)
    # Distance transform for robust center
    mask_dt = (mask > 0).astype(np.uint8) * 255
    dt = cv2.distanceTransform(mask_dt, cv2.DIST_L2, 5)
    _, _, _, maxLoc = cv2.minMaxLoc(dt)
    return (int(maxLoc[0]), int(maxLoc[1])), mask

# ---------------- Kalman Filter ----------------
def create_kalman():
    kf = cv2.KalmanFilter(4, 2)
    kf.transitionMatrix = np.array([[1, 0, 1, 0],
                                     [0, 1, 0, 1],
                                     [0, 0, 1, 0],
                                     [0, 0, 0, 1]], np.float32)
    kf.measurementMatrix = np.array([[1, 0, 0, 0],
                                      [0, 1, 0, 0]], np.float32)
    kf.processNoiseCov = np.eye(4, dtype=np.float32) * 1e-2
    kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 1e-1
    kf.errorCovPost = np.eye(4, dtype=np.float32)
    return kf

kalman = create_kalman()
initialized = False

# ---------------- Main ----------------
camera = PiCamera()
ret, frame = camera.read()
cv2.namedWindow("ROI Selection")
cv2.setMouseCallback("ROI Selection", mouse_callback, param=frame)

print("Click 4 points to define ROI...")

# ROI selection loop
while roi_mask is None:
    ret, frame = camera.read()
    if not ret:
        break
    temp = frame.copy()
    for pt in roi_points:
        cv2.circle(temp, pt, 5, (0, 0, 255), -1)
    cv2.imshow("ROI Selection", temp)
    if cv2.waitKey(10) & 0xFF == 27:  # ESC to quit
        break

cv2.destroyWindow("ROI Selection")

# Main tracking loop
try:
    while True:
        ret, frame = camera.read()
        if not ret:
            break

        measurement, mask = track_magnet(frame)

        if measurement is not None:
            mx, my = measurement
            meas = np.array([[np.float32(mx)], [np.float32(my)]])
            if not initialized:
                kalman.statePost = np.array([[mx], [my], [0], [0]], np.float32)
                initialized = True
            prediction = kalman.correct(meas)
        else:
            prediction = kalman.predict()

        px, py = int(prediction[0]), int(prediction[1])
        cv2.circle(frame, (px, py), 8, (255, 0, 0), 2)
        cv2.putText(frame, f"Tracked: ({px},{py})", (px+10, py),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 1)

        cv2.imshow("Magnet Tracking", frame)
        cv2.imshow("Threshold Mask", mask)

        if cv2.waitKey(10) & 0xFF == 27:
            break
finally:
    camera.release()
    cv2.destroyAllWindows()
