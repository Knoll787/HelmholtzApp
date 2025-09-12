import image_processing 

camera = image_processing.PiCamera()
ret, first_frame = camera.read()
if not ret:
    raise RuntimeError("Could not read first frame from PiCamera")

try:
    while True:
        ret, frame = camera.read()
        if not ret:
            break

        image_processing.cv2.imshow("Camera Feed", frame)

        # Exit on ESC
        if image_processing.cv2.waitKey(10) & 0xFF == 27:
            break
finally:
    camera.release()
    image_processing.cv2.destroyAllWindows()
    print("Exited cleanly.")
