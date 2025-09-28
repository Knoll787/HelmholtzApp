import cv2
import numpy as np
from picamera2 import Picamera2
from libcamera import Transform


import argparse
import image_processing as ip 
import movement as mv
import controllers as ctlr
import time
import os

# ---------------- ROI Selection ----------------
roi_points = []
roi_mask = None

def mouse_callback(event, x, y, flags, param):
    global roi_points, roi_mask
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
initialized = False

# ---------------- Main ----------------
camera = ip.PiCamera()
ret, first_frame = camera.read()
if not ret:
    raise RuntimeError("Could not read first frame from PiCamera")

# Setup ROI selection using the first frame shape
cv2.namedWindow("ROI Selection")
cv2.setMouseCallback("ROI Selection", mouse_callback, param=first_frame)

print("Click 4 corners (in clockwise or counterclockwise order) of the workspace polygon.")
print("After the 4th click, ROI selection window will close and tracking will start.")

# ROI selection loop
while roi_mask is None:
    ret, frame = camera.read()
    if not ret:
        break
    tmp = frame.copy()
    # draw current points for guidance
    for p in roi_points:
        cv2.circle(tmp, p, 6, (0, 0, 255), -1)
    if len(roi_points) >= 2:
        cv2.polylines(tmp, [np.array(roi_points, dtype=np.int32)], isClosed=False, color=(0,255,255), thickness=1)
    cv2.imshow("ROI Selection", tmp)
    if cv2.waitKey(10) & 0xFF == 27:
        print("ROI selection cancelled by user. Exiting.")
        camera.release()
        cv2.destroyAllWindows()
        raise SystemExit

cv2.destroyWindow("ROI Selection")
print("Starting tracking...")

# ---------------- Tracking loop ----------------


ret, first_frame = camera.read()
if not ret:
    raise RuntimeError("Could not read first frame from PiCamera")

ret, first_frame = camera.read()
if not ret:
    raise RuntimeError("Could not read first frame from PiCamera")

try:
    x = mv.Coil(FWD=17, BWD=27) 
    y = mv.Coil(FWD=13, BWD=5) 
    
    # Simulation Configuration
    #target = (263, 95)  # Test Position x axis 
    target = (127, 253)  # Test Position y axis 
    ctl_x = ctlr.PID("x", kp=1.00, ki=0.10, kd=0.00, setpoint=target[0], output_limits=(-100, 100))
    ctl_y = ctlr.PID("y", kp=1.00, ki=0.10, kd=0.00, setpoint=target[1], output_limits=(-100, 100))
    

    while True:
        ret, frame = camera.read()
        if not ret:
            break

        #comp_mask = ip.mask(frame, roi_points=[(101,95), (424,87), (431,415), (105,422)])
        comp_mask = ip.mask(frame, roi_points=roi_points)
        pos = ip.track(comp_mask, min_area=500)
        if pos is None:
            print("Warning: No valid object found. Skipping frame.")
            continue 

        
        """
        #pid_x_out = ctl_x.compute(pos[0])
        #pid_y_out = ctl_y.compute(pos[1])
        #pid_x_out = ctl_x.step(pos[0])
        pid_y_out = ctl_y.step(pos[1])

        #x.set_magnetic_field(pid_x_out) 
        y.set_magnetic_field(pid_y_out) 
        """

        ip.cv2.circle(frame, (target[0], target[1]), radius=5, color=(0, 0, 255), thickness=1)
        ip.cv2.circle(frame, (pos[0], pos[1]), radius=5, color=(255, 0, 0), thickness=1)
        ip.cv2.imshow("Camera Feed", frame)
        ip.cv2.imshow("Mask", comp_mask)

        # Exit on ESC
        if ip.cv2.waitKey(10) & 0xFF == 27:
            break
finally:
    camera.release()
    x.cleanup()
    ip.cv2.destroyAllWindows()
    print("Exited cleanly.")
