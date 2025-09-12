import image_processing as ip 

camera = ip.PiCamera()
ret, first_frame = camera.read()
if not ret:
    raise RuntimeError("Could not read first frame from PiCamera")

try:
    while True:
        ret, frame = camera.read()
        if not ret:
            break

        comp_mask = ip.mask(frame, roi_points=[(101,95), (424,87), (431,415), (105,422)])
        ip.cv2.imshow("Camera Feed", frame)
        ip.cv2.imshow("Masking Feed", comp_mask)
        print(ip.track(comp_mask, min_area=500))


        # Exit on ESC
        if ip.cv2.waitKey(10) & 0xFF == 27:
            break
finally:
    camera.release()
    ip.cv2.destroyAllWindows()
    print("Exited cleanly.")
