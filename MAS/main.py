import argparse
import image_processing as ip 
import movement as mv
import controllers as ctlr
import time

camera = ip.PiCamera()
ret, first_frame = camera.read()
if not ret:
    raise RuntimeError("Could not read first frame from PiCamera")

try:

    x = mv.Coil(FWD=17, BWD=27) 
    y = mv.Coil(FWD=13, BWD=5) 
    
    # Simulation Configuration
    target = (142, 137)  # Target position in pixels (x, y)
    ctl_x = ctlr.PID(kp=0.10, ki=0.01, kd=0.00, setpoint=target[0], output_limits=(-50, 50))
    ctl_y = ctlr.PID(kp=0.10, ki=0.01, kd=0.00, setpoint=target[1], output_limits=(-50, 50))
    

    while True:
        ret, frame = camera.read()
        if not ret:
            break

        comp_mask = ip.mask(frame, roi_points=[(101,95), (424,87), (431,415), (105,422)])
        pos = ip.track(comp_mask, min_area=500)
        pid_x_out = ctl_x.compute(pos[0])
        pid_y_out = ctl_y.compute(pos[1])
        x.set_magnetic_field(pid_x_out) 
        y.set_magnetic_field(pid_y_out) 

        ip.cv2.circle(frame, (target[0], target[1]), radius=5, color=(0, 0, 255), thickness=1)
        ip.cv2.circle(frame, pos, radius=5, color=(255, 0, 0), thickness=1)
        ip.cv2.imshow("Camera Feed", frame)

        # Exit on ESC
        if ip.cv2.waitKey(10) & 0xFF == 27:
            break
finally:
    camera.release()
    x.cleanup()
    ip.cv2.destroyAllWindows()
    print("Exited cleanly.")