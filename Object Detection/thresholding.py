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
roi_points = [(101,95), (424,87), (431,415), (105,422)]  # default points for quick testing
roi_mask = None
#roi_points = []  # default points for quick testing
#roi_mask = None
test = None

def mouse_callback(event, x, y, flags, param):
    global roi_points, roi_mask
    """ Enable manual ROI selection by clicking 4 points in the displayed frame.
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(roi_points) < 4:
            roi_points.append((x, y))
            print(f"Point {len(roi_points)}: {(x,y)}")
        if len(roi_points) == 4:
            # Create polygon mask with the same shape as the passed param frame
            h, w = param.shape[:2]
            mask = np.zeros((h, w), dtype=np.uint8)
            cv2.fillPoly(mask, [np.array(roi_points, dtype=np.int32)], 255)
            roi_mask = mask
            print("ROI set. Closing ROI selection window...")
            print(roi_points)
        """
    # Create polygon mask with the same shape as the passed param frame
    h, w = param.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(mask, [np.array(roi_points, dtype=np.int32)], 255)
    roi_mask = mask
    print("ROI set. Closing ROI selection window...")
    print(roi_points)

# ---------------- Magnet tracking (centroid-of-white-object) ----------------
def track_magnet(frame,
                 lower_black=(0, 0, 0),
                 upper_black=(180, 255, 95),
                 min_area=500,
                 hole_fill=True):
    """
    Returns (cx, cy) = centroid of the white object in the final mask (or None),
    and the mask used (single-channel uint8).
    """
    global roi_mask

    # 1) HSV threshold for dark/black
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower_black), np.array(upper_black))
    # 2) Restrict to ROI if provided
    if roi_mask is not None:
        mask = cv2.bitwise_and(mask, roi_mask)
    global test
    test = mask.copy()

    # 3) Morphological cleanup
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)

    test = mask.copy()
    """
    # 4) Fill holes so interior becomes continuous
    if hole_fill:
        im_inv = cv2.bitwise_not(mask)
        h, w = im_inv.shape[:2]
        im_floodfill = im_inv.copy()
        mask_ff = np.zeros((h + 2, w + 2), np.uint8)
        cv2.floodFill(im_floodfill, mask_ff, (0, 0), 255)
        im_floodfill_inv = cv2.bitwise_not(im_floodfill)
        mask = cv2.bitwise_or(mask, im_floodfill_inv)
    """

    # 5) Find contours and keep only sufficiently large ones
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid = [c for c in contours if cv2.contourArea(c) >= min_area]
    if not valid:
        return None, mask

    # 6) Take the largest contour (assumed to be the magnet)
    c = max(valid, key=cv2.contourArea)
    area = cv2.contourArea(c)

    # 7) Create a single filled mask for that contour (white object mask)
    comp_mask = np.zeros_like(mask)
    cv2.drawContours(comp_mask, [c], -1, 255, thickness=-1)

    # 8) Compute centroid from the filled (white) object mask using moments
    M = cv2.moments(comp_mask)
    centroid = None
    if M["m00"] != 0:
        cx = int(round(M["m10"] / M["m00"]))
        cy = int(round(M["m01"] / M["m00"]))
        centroid = (cx, cy)

    # 9) Fallbacks (if centroid failed) — distance transform or minEnclosingCircle
    if centroid is None:
        # distance transform center
        dt = cv2.distanceTransform((comp_mask > 0).astype(np.uint8), cv2.DIST_L2, 5)
        _, maxVal, _, maxLoc = cv2.minMaxLoc(dt)
        if maxVal > 0:
            centroid = (int(round(maxLoc[0])), int(round(maxLoc[1])))
        else:
            # final fallback: min enclosing circle center
            (xc, yc), radius = cv2.minEnclosingCircle(c)
            centroid = (int(round(xc)), int(round(yc)))

    return centroid, comp_mask

# ---------------- Kalman Filter (pos+vel) ----------------
def create_kalman():
    kf = cv2.KalmanFilter(4, 2)
    # state: x, y, vx, vy
    kf.transitionMatrix = np.array([[1, 0, 1, 0],
                                    [0, 1, 0, 1],
                                    [0, 0, 1, 0],
                                    [0, 0, 0, 1]], dtype=np.float32)
    kf.measurementMatrix = np.array([[1, 0, 0, 0],
                                     [0, 1, 0, 0]], dtype=np.float32)
    kf.processNoiseCov = np.eye(4, dtype=np.float32) * 1e-2
    kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 1e-1
    kf.errorCovPost = np.eye(4, dtype=np.float32)
    return kf

kalman = create_kalman()
initialized = False

# ---------------- Main ----------------
camera = PiCamera()
ret, first_frame = camera.read()
if not ret:
    raise RuntimeError("Could not read first frame from PiCamera")

# Setup ROI selection using the first frame shape
cv2.namedWindow("ROI Selection")
cv2.setMouseCallback("ROI Selection", mouse_callback, param=first_frame)

# ROI selection loop
while roi_mask is None:
    ret, frame = camera.read()
    if not ret:
        break
    tmp = frame.copy()
    # draw current points for guidance
    for p in roi_points:
        cv2.circle(tmp, p, 2, (255, 0, 127), -1)
    if len(roi_points) >= 2:
        cv2.polylines(tmp, [np.array(roi_points, dtype=np.int32)], isClosed=True, color=(0,0,0), thickness=1)
    cv2.imshow("ROI Selection", tmp)
    if cv2.waitKey(10) & 0xFF == 27:
        print("ROI selection cancelled by user. Exiting.")
        camera.release()
        cv2.destroyAllWindows()
        raise SystemExit

cv2.destroyWindow("ROI Selection")
print("Starting tracking...")

# ---------------- Tracking loop ----------------
try:
    while True:
        ret, frame = camera.read()
        if not ret:
            break

        # tune these if needed
        LOWER_BLACK = (0, 0, 0)
        UPPER_BLACK = (180, 255, 95)   # per your request
        MIN_AREA = 300                 # tune to magnet pixel size

        measurement, comp_mask = track_magnet(frame,
                                             lower_black=LOWER_BLACK,
                                             upper_black=UPPER_BLACK,
                                             min_area=MIN_AREA,
                                             hole_fill=True)

        # draw the white object mask (resized view if needed)
        cv2.imshow("Test Output", test)
        #cv2.imshow("Component Mask (white object)", comp_mask)

        if measurement is not None:
            mx, my = measurement
            # draw raw centroid (moments) in green
            cv2.circle(frame, (mx, my), 6, (0, 255, 0), -1)
            cv2.putText(frame, f"Raw centroid: ({mx},{my})", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

            meas = np.array([[np.float32(mx)], [np.float32(my)]])
            if not initialized:
                # initialize Kalman state with zero velocity
                kalman.statePost = np.array([[mx], [my], [0], [0]], dtype=np.float32)
                initialized = True
            # correct with measurement
            corrected = kalman.correct(meas)
            px, py = int(round(corrected[0,0])), int(round(corrected[1,0]))
        else:
            # no measurement -> predict only
            pred = kalman.predict()
            px, py = int(round(pred[0,0])), int(round(pred[1,0]))
            cv2.putText(frame, "No measurement (predicting)", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)

        # draw Kalman-smoothed/predicted position in blue
        cv2.circle(frame, (px, py), 6, (255, 0, 0), 2)
        cv2.putText(frame, f"Filtered: ({px},{py})", (frame.shape[0]-10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 1)

        # show ROI overlay
        if roi_mask is not None:
            # outline the ROI polygon
            pts = np.array(roi_points, dtype=np.int32).reshape((-1,1,2))
            cv2.polylines(frame, [pts], isClosed=True, color=(0,255,255), thickness=2)

        cv2.imshow("Magnet Tracking (overlay)", frame)

        if cv2.waitKey(10) & 0xFF == 27:
            break

finally:
    camera.release()
    cv2.destroyAllWindows()
    print("Exited cleanly.")
