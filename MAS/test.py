import math
import threading
import time
import sys
import sdl2
import RPi.GPIO as GPIO

class RotatingFieldController:
    def __init__(self):
        # Initialize GPIO pins for 3 coils (X, Y, Z)
        self.PINS = {
            "X_FWD": 17, "X_BWD": 27,
            "Y_FWD": 13, "Y_BWD": 5,
            "Z_FWD": 22, "Z_BWD": 23
        }

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in self.PINS.values():
            GPIO.setup(pin, GPIO.OUT)

        self.pwm = {
            "x_fwd": GPIO.PWM(self.PINS["X_FWD"], 1000),
            "x_bwd": GPIO.PWM(self.PINS["X_BWD"], 1000),
            "y_fwd": GPIO.PWM(self.PINS["Y_FWD"], 1000),
            "y_bwd": GPIO.PWM(self.PINS["Y_BWD"], 1000),
            "z_fwd": GPIO.PWM(self.PINS["Z_FWD"], 1000),
            "z_bwd": GPIO.PWM(self.PINS["Z_BWD"], 1000),
        }

        for pwm in self.pwm.values():
            pwm.start(0)

        # Rotation parameters
        self.MAX_PWM = 60.0     # duty cycle cap
        self.B_amplitude = 50.0 # % of MAX_PWM
        self.rotation_freq = 1.0  # Hz
        self.rotation_plane = "XY"  # default plane
        self.direction = 1  # +1 = CCW, -1 = CW
        self.rotating = False
        self.rotation_thread = None

        # Initialize SDL joystick
        sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK)
        if sdl2.SDL_NumJoysticks() < 1:
            print("No controller detected!")
            sys.exit()
        self.joystick = sdl2.SDL_JoystickOpen(0)
        print("Connected:", sdl2.SDL_JoystickName(self.joystick).decode())

        # Controller button mappings
        self.BTN_ROTATE = 0  # e.g. 'A' button
        self.BTN_PLANE = 1   # e.g. 'B' button
        self.BTN_DIR = 2     # e.g. 'X' button

    # ---------------- Field Control ----------------

    def set_field(self, bx, by, bz):
        """Set magnetic field PWM on all three axes."""
        for axis, val in zip(("x", "y", "z"), (bx, by, bz)):
            fwd = self.pwm[f"{axis}_fwd"]
            bwd = self.pwm[f"{axis}_bwd"]

            if val > 0:
                fwd.ChangeDutyCycle(min(val, self.MAX_PWM))
                bwd.ChangeDutyCycle(0)
            elif val < 0:
                fwd.ChangeDutyCycle(0)
                bwd.ChangeDutyCycle(min(abs(val), self.MAX_PWM))
            else:
                fwd.ChangeDutyCycle(0)
                bwd.ChangeDutyCycle(0)

    # ---------------- Rotation ----------------

    def rotate_field(self):
        """Background thread: continuously rotates the magnetic field."""
        t0 = time.time()
        while self.rotating:
            t = time.time() - t0
            omega = 2 * math.pi * self.rotation_freq * self.direction
            B = self.B_amplitude

            # Select plane
            if self.rotation_plane == "XY":
                bx = B * math.sin(omega * t)
                by = B * math.cos(omega * t)
                bz = 0
            elif self.rotation_plane == "XZ":
                bx = B * math.sin(omega * t)
                by = 0
                bz = B * math.cos(omega * t)
            elif self.rotation_plane == "YZ":
                bx = 0
                by = B * math.sin(omega * t)
                bz = B * math.cos(omega * t)
            else:
                bx = by = bz = 0

            self.set_field(bx, by, bz)
            time.sleep(0.01)

    def start_rotation(self):
        if self.rotating:
            return
        print(f"\n▶ Starting rotation in {self.rotation_plane} plane, "
              f"{'CCW' if self.direction>0 else 'CW'}, {self.rotation_freq:.2f} Hz")
        self.rotating = True
        self.rotation_thread = threading.Thread(target=self.rotate_field)
        self.rotation_thread.start()

    def stop_rotation(self):
        if not self.rotating:
            return
        print("\n⏹ Stopping rotation...")
        self.rotating = False
        self.rotation_thread.join()
        self.set_field(0, 0, 0)

    # ---------------- Controller ----------------

    def poll_controller(self):
        event = sdl2.SDL_Event()
        while sdl2.SDL_PollEvent(event):
            if event.type == sdl2.SDL_JOYBUTTONDOWN:
                btn = event.jbutton.button

                if btn == self.BTN_ROTATE:
                    if not self.rotating:
                        self.start_rotation()
                    else:
                        self.stop_rotation()

                elif btn == self.BTN_PLANE:
                    # Cycle through planes
                    planes = ["XY", "XZ", "YZ"]
                    idx = planes.index(self.rotation_plane)
                    self.rotation_plane = planes[(idx + 1) % len(planes)]
                    print(f"\nRotation plane set to: {self.rotation_plane}")

                elif btn == self.BTN_DIR:
                    self.direction *= -1
                    print(f"\nRotation direction: {'CCW' if self.direction>0 else 'CW'}")

            elif event.type == sdl2.SDL_JOYAXISMOTION:
                # Adjust rotation frequency using joystick Y-axis
                if event.jaxis.axis == 1:
                    val = event.jaxis.value / 32767.0
                    self.rotation_freq = max(0.1, min(5.0, abs(val) * 5))
                    print(f"\rRotation freq: {self.rotation_freq:.2f} Hz", end="", flush=True)

    def cleanup(self):
        self.stop_rotation()
        for pwm in self.pwm.values():
            pwm.stop()
        GPIO.cleanup()
        sdl2.SDL_Quit()


# ---------------- MAIN LOOP ----------------
if __name__ == "__main__":
    try:
        controller = RotatingFieldController()
        print("Controls:")
        print(" A → toggle rotation")
        print(" B → change rotation plane (XY, XZ, YZ)")
        print(" X → reverse direction (CW/CCW)")
        print(" Left stick Y → adjust frequency (0.1–5 Hz)\n")

        while True:
            controller.poll_controller()
            time.sleep(0.05)

    except KeyboardInterrupt:
        controller.cleanup()
        print("\nExiting safely...")
