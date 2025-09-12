import camera

cam = camera.PiCamera()
ret, first_frame = cam.read()
if not ret:
    raise RuntimeError("Could not read first frame from PiCamera")

try:
    while True:
        ret, frame = cam.read()
        if not ret:
            break

        cv2.imshow("Camera Feed", frame)

        # Exit on ESC
        if cv2.waitKey(10) & 0xFF == 27:
            break
finally:
    cam.release()
    cv2.destroyAllWindows()
    print("Exited cleanly.")
