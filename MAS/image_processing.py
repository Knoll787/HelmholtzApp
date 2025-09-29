"""
import cv2
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


# Creates the mask that will be used to calculate the position of the agent 
def mask(frame, roi_points):
    # Masking - Region of Interest (ROI)
    roi_points = [(101,95), (424,87), (431,415), (105,422)]  # Region of interest points 
    h, w = frame.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(mask, [np.array(roi_points, dtype=np.int32)], 255)
    roi_mask = mask
    
    # Masking - Thresholding
    lower_black = (0, 0, 0)
    upper_black = (180, 255, 95)
    min_area = 500
    hole_fill = True
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower_black), np.array(upper_black))
    
    # Masking - Combine ROI and Thresholding
    if roi_mask is not None:
        mask = cv2.bitwise_and(mask, roi_mask)
        
    # Masking - Morphological cleanup
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close) 
    
    return mask

def track(mask, min_area):
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid = [c for c in contours if cv2.contourArea(c) >= min_area]
    if not valid:
        return (0,0) 
    
    # Determine the largest contour
    c = max(valid, key=cv2.contourArea)
    area = cv2.contourArea(c)
    
    # Calculate centroid
    M = cv2.moments(mask)
    centroid = None
    if M["m00"] != 0:
        cx = int(round(M["m10"] / M["m00"]))
        cy = int(round(M["m01"] / M["m00"]))
        centroid = (cx, cy)

    return centroid

def calculate_error(agent_pos, point):
    x_error = agent_pos[0] - point[0]
    y_error = agent_pos[1] - point[1]
    abs_error = (x_error**2 + y_error**2)**0.5 
    
    return (x_error, y_error, abs_error)

"""
import cv2
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
    def __init__(self, resolution=(640, 640), vflip=True):
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"format": "BGR888", "size": resolution}
        )
        self.picam2.configure(config)

        # Apply optional transform
        transform = Transform(vflip=int(vflip))
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


# --- Image Processing Functions ---

def mask(frame, roi_points=None):
    """
    Generate a mask of the ROI with black color thresholding.
    roi_points: list of 4 (x, y) tuples for polygon ROI.
    """
    h, w = frame.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)

    if roi_points is not None and len(roi_points) >= 3:
        cv2.fillPoly(mask, [np.array(roi_points, dtype=np.int32)], 255)
        roi_mask = mask
    else:
        roi_mask = None

    # HSV thresholding for black-ish colors
    lower_black = (0, 0, 0)
    upper_black = (180, 255, 95)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    thresh = cv2.inRange(hsv, np.array(lower_black), np.array(upper_black))

    if roi_mask is not None:
        thresh = cv2.bitwise_and(thresh, roi_mask)

    # Morphological cleanup
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_open)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_close)

    return thresh


def track(mask, min_area=500):
    """
    Track largest valid contour and return centroid.
    Returns (x, y) or None if nothing is found.
    """
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid = [c for c in contours if cv2.contourArea(c) >= min_area]
    if not valid:
        return None

    # Largest contour
    c = max(valid, key=cv2.contourArea)
    M = cv2.moments(c)
    if M["m00"] != 0:
        cx = int(round(M["m10"] / M["m00"]))
        cy = int(round(M["m01"] / M["m00"]))
        return (cx, cy)
    return None


def calculate_error(agent_pos, point):
    """
    Compute error between current agent position and target point.
    Returns (x_error, y_error, abs_error).
    """
    if agent_pos is None or point is None:
        return None

    x_error = agent_pos[0] - point[0]
    y_error = agent_pos[1] - point[1]
    abs_error = (x_error**2 + y_error**2) ** 0.5
    return (x_error, y_error, abs_error)
