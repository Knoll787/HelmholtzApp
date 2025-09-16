import image_processing as ip 
import movement as mv
import controllers as ctlr

camera = ip.PiCamera()
ret, first_frame = camera.read()
if not ret:
    raise RuntimeError("Could not read first frame from PiCamera")

try:
    ctl = mv.Gamepad()
    while True:
        ret, frame = camera.read()
        if not ret:
            break

        comp_mask = ip.mask(frame, roi_points=[(101,95), (424,87), (431,415), (105,422)])
        ip.cv2.imshow("Camera Feed", frame)
        ctl.poll_controller()

        # Exit on ESC
        if ip.cv2.waitKey(10) & 0xFF == 27:
            break
finally:
    camera.release()
    ctl.cleanup()
    ip.cv2.destroyAllWindows()
    print("Exited cleanly.")
