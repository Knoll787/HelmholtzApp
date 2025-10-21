import argparse
import image_processing as ip 
import movement as mv
import controllers as ctlr
import time
import os

os.remove("../data/test.csv") if os.path.exists("../data/test.csv") else None
camera = ip.PiCamera()
ret, first_frame = camera.read()
if not ret:
    raise RuntimeError("Could not read first frame from PiCamera")

try:
    x = mv.Coil(FWD=17, BWD=27) 
    y = mv.Coil(FWD=13, BWD=5) 
    
    # Simulation Configuration
    target = (308, 59)  # Test Position x axis 
    #target = (145, 213)  # Test Position y axis 
    ctl_x = ctlr.PID("x", kp=4.00, ki=00.0000, kd=0.0000, setpoint=target[0], output_limits=(-60, 60))
    #ctl_y = ctlr.PID("y", kp=10.8, ki=79.4118, kd=0.3672, setpoint=target[1], output_limits=(-60, 60))
    

    while True:
        ret, frame = camera.read()
        if not ret:
            break

        comp_mask = ip.mask(frame, roi_points=[(145,59), (470, 59), (145, 379), (470, 379)])
        pos = ip.track(comp_mask, min_area=500)
        if pos is None:
            print("Warning: No valid object found. Skipping frame.")
            continue 

        
        pid_x_out = ctl_x.compute(pos[0])
        #pid_y_out = ctl_y.compute(pos[1])

        x.set_magnetic_field(pid_x_out) 
        #y.set_magnetic_field(pid_y_out) 

        ip.cv2.circle(frame, (target[0], target[1]), radius=5, color=(0, 0, 255), thickness=1)
        ip.cv2.circle(frame, (pos[0], pos[1]), radius=5, color=(255, 0, 0), thickness=1)
        ip.cv2.imshow("Camera Feed", frame)
        #ip.cv2.imshow("Camera Feed", comp_mask)

        # Exit on ESC
        if ip.cv2.waitKey(10) & 0xFF == 27:
            break
finally:
    camera.release()
    x.cleanup()
    ip.cv2.destroyAllWindows()
    print("Exited cleanly.")