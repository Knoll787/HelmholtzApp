import image_processing as ip 
import movement as mv
import controllers as ctlr

camera = ip.PiCamera()
ret, first_frame = camera.read()
if not ret:
    raise RuntimeError("Could not read first frame from PiCamera")

try:
    x = mv.Coil(FWD=17, BWD=27) 
    y = mv.Coil(FWD=13, BWD=5) 
    
    ctl_x = ctlr.PID(kp=0.10, ki=0.01, kd=0.00, setpoint=142, output_limits=(-50, 50))
    ctl_y = ctlr.PID(kp=0.10, ki=0.01, kd=0.00, setpoint=137, output_limits=(-50, 50))
    while True:
        ret, frame = camera.read()
        if not ret:
            break

        comp_mask = ip.mask(frame, roi_points=[(101,95), (424,87), (431,415), (105,422)])
        pos = ip.track(comp_mask, min_area=500)
        x.set_magnetic_field(ctl_x.compute(pos[0])) 
        y.set_magnetic_field(ctl_y.compute(pos[1])) 

        ip.cv2.imshow("Camera Feed", frame)

        # Exit on ESC
        if ip.cv2.waitKey(10) & 0xFF == 27:
            break
finally:
    camera.release()
    x.cleanup()
    ip.cv2.destroyAllWindows()
    print("Exited cleanly.")
