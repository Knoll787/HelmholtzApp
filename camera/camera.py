import cv2
import time
import numpy as np
from picamera2 import Picamera2

# Initialize both cameras
cam0 = Picamera2(0)
cam1 = Picamera2(1)

# Configure both cameras for BGR output (needed for OpenCV)
config0 = cam0.create_preview_configuration(main={"format": "BGR888", "size": (640, 480)})
config1 = cam1.create_preview_configuration(main={"format": "BGR888", "size": (640, 480)})

cam0.configure(config0)
cam1.configure(config1)

# Start the cameras
cam0.start()
cam1.start()

# Let them warm up
time.sleep(2)

# Main loop
while True:
    # Capture a frame from each camera
    frame0 = cam0.capture_array()
    frame1 = cam1.capture_array()

    # Convert both frames to grayscale
    gray0 = cv2.cvtColor(frame0, cv2.COLOR_BGR2GRAY)
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)

    # Optional: convert grayscale back to 3-channel to allow stacking
    gray0_3ch = cv2.cvtColor(gray0, cv2.COLOR_GRAY2BGR)
    gray1_3ch = cv2.cvtColor(gray1, cv2.COLOR_GRAY2BGR)

    # Combine both frames side-by-side
    combined = np.hstack((gray0_3ch, gray1_3ch))

    # Display the combined frame
    cv2.imshow("Dual HQ Camera - Grayscale", combined)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cv2.destroyAllWindows()
cam0.stop()
cam1.stop()
