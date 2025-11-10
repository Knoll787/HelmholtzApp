#!/usr/bin/env python3
import math
import threading
import time
import sys
import sdl2
import RPi.GPIO as GPIO

class MDD10A_DualCoilController:
    """
    3-axis controller for dual-coil-per-axis MDD10A wiring.
    Each axis uses two MDD10A channels (DIR1/PWM1 and DIR2/PWM2).
    Both channels for an axis are driven identically.
    """

    def __init__(self):
        # ---------------- PIN MAPPING (from your pinout)
        # Motor Driver 3 - X coils
        # DIR1 GPIO22, PWM1 GPIO17, DIR2 GPIO23, PWM2 GPIO27
        # Motor Driver 2 - Y coils
        # DIR1 GPIO6,  PWM1 GPIO5,  DIR2 GPIO19, PWM2 GPIO13
        # Motor Driver 1 - Z coils
        # DIR1 GPIO16, PWM1 GPIO12, DIR2 GPIO21, PWM2 GPIO20

        self.PINS = {
            # X axis (driver 3)
            "X_DIR1": 22, "X_PWM1": 17,
            "X_DIR2": 23, "X_PWM2": 27,
            # Y axis (driver 2)
            "Y_DIR1": 6,  "Y_PWM1": 5,
            "Y_DIR2": 19, "Y_PWM2": 13,
            # Z axis (driver 1)
            "Z_DIR1": 16, "Z_PWM1": 12,
            "Z_DIR2": 21, "Z_PWM2": 20,
        }

        # PWM frequency
        self.PWM_FREQ = 1000  # Hz

        # GPIO setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in self.PINS.values():
            GPIO.setup(pin, GPIO.OUT)

        # Create PWM objects for every PWM pin (six PWMs)
        self.pwm = {
            "X1": GPIO.PWM(self.PINS["X_PWM1"], self.PWM_FREQ),
            "X2": GPIO.PWM(self.PINS["X_PWM2"], self.PWM_FREQ),
            "Y1": GPIO.PWM(self.PINS["Y_PWM1"], self.PWM_FREQ),
            "Y2": GPIO.PWM(self.PINS["Y_PWM2"], self.PWM_FREQ),
            "Z1": GPIO.PWM(self.PINS["Z_PWM1"], self.PWM_FREQ),
            "Z2": GPIO.PWM(self.PINS["Z_PWM2"], self.PWM_FREQ),
        }
        for p in self.pwm.values():
            p.start(0)

        # DIR pins grouped per axis (two DIR pins per axis)
        self.dir_pins = {
            "X": (self.PINS["X_DIR1"], self.PINS["X_DIR2"]),
            "Y": (self.PINS["Y_DIR1"], self.PINS["Y_DIR2"]),
            "Z": (self.PINS["Z_DIR1"], self.PINS["Z_DIR2"]),
        }

        # PWM objects grouped per axis (two PWMs per axis)
        self.pwm_pairs = {
            "X": (self.pwm["X1"], self.pwm["X2"]),
            "Y": (self.pwm["Y1"], self.pwm["Y2"]),
            "Z": (self.pwm["Z1"], self.pwm["Z2"]),
        }

        # Rotation / field parameters
        self.MAX_PWM = 60.0       # safety duty-cycle cap (%) - both PWMs clipped to this
        self.B_amplitude = 50.0   # amplitude used by generator (%)
        self.rotation_freq = 1.0  # Hz default
        self.rotation_mode = "XY" # "X","Y","Z","XY","XZ","YZ"
        self.direction = 1        # +1 CCW, -1 CW
        self.rotating = False
        self.rotation_thread = None

        # Initialize joystick (optional)
        sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK)
        if sdl2.SDL_NumJoysticks() < 1:
            print("No controller detected! (SDL Joystick)")
            self.joystick = None
        else:
            self.joystick = sdl2.SDL_JoystickOpen(0)
            print("Connected:", sdl2.SDL_JoystickName(self.joystick).decode())

        # Controller mapping (adjust indices to your controller)
        self.BTN_ROTATE = 0  # toggle start/stop
        self.BTN_MODE   = 1  # cycle modes (X,Y,Z,XY,XZ,YZ)
        self.BTN_DIR    = 2  # reverse direction

    # ---------------- Low-level axis control ----------------
    def _apply_axis(self, axis, duty_percent):
        """
        axis: "X"|"Y"|"Z"
        duty_percent: -100 .. +100 (negative => reverse direction)
        Sets BOTH DIR pins and BOTH PWM outputs for the axis identically.
        """
        if axis not in ("X", "Y", "Z"):
            return

        dir1, dir2 = self.dir_pins[axis]
        pwm1, pwm2 = self.pwm_pairs[axis]

        # Constrain magnitude
        mag = min(abs(duty_percent), self.MAX_PWM)

        if duty_percent > 0:
            # Positive direction: set DIR pins HIGH and both PWMs to mag
            GPIO.output(dir1, GPIO.HIGH)
            GPIO.output(dir2, GPIO.HIGH)
            pwm1.ChangeDutyCycle(mag)
            pwm2.ChangeDutyCycle(mag)
        elif duty_percent < 0:
            # Negative direction: set DIR pins LOW and both PWMs to mag
            GPIO.output(dir1, GPIO.LOW)
            GPIO.output(dir2, GPIO.LOW)
            pwm1.ChangeDutyCycle(mag)
            pwm2.ChangeDutyCycle(mag)
        else:
            # Zero: stop PWMs and set DIRs low
            pwm1.ChangeDutyCycle(0)
            pwm2.ChangeDutyCycle(0)
            GPIO.output(dir1, GPIO.LOW)
            GPIO.output(dir2, GPIO.LOW)

    def set_field(self, bx, by, bz):
        """
        Set instantaneous magnetic 'amplitudes' on X, Y, Z axes.
        Values are treated as PWM percent and may be negative (direction).
        Example: bx = +30 -> both X coils driven at +30% duty.
        """
        # clip inputs to safe range of -MAX_PWM .. +MAX_PWM (optional)
        self._apply_axis("X", bx)
        self._apply_axis("Y", by)
        self._apply_axis("Z", bz)

    # ---------------- Rotation / Oscillation Generator ----------------
    def rotate_field(self):
        t0 = time.time()
        while self.rotating:
            t = time.time() - t0
            omega = 2 * math.pi * self.rotation_freq * self.direction
            B = self.B_amplitude

            bx = by = bz = 0.0

            if self.rotation_mode == "XY":
                bx =  B * math.sin(omega * t)
                by =  B * math.cos(omega * t)
            elif self.rotation_mode == "XZ":
                bx =  B * math.sin(omega * t)
                bz =  B * math.cos(omega * t)
            elif self.rotation_mode == "YZ":
                by =  B * math.sin(omega * t)
                bz =  B * math.cos(omega * t)
            elif self.rotation_mode == "X":
                bx =  B * math.sin(omega * t)
            elif self.rotation_mode == "Y":
                by =  B * math.sin(omega * t)
            elif self.rotation_mode == "Z":
                bz =  B * math.sin(omega * t)

            # Apply same commands to both coils per axis
            self.set_field(bx, by, bz)

            time.sleep(0.001)  # ~1000 Hz update

    def start_rotation(self):
        if self.rotating:
            return
        print(f"\nStarting: mode={self.rotation_mode}, dir={'CCW' if self.direction>0 else 'CW'}, "
              f"freq={self.rotation_freq:.2f} Hz")
        self.rotating = True
        self.rotation_thread = threading.Thread(target=self.rotate_field, daemon=True)
        self.rotation_thread.start()

    def stop_rotation(self):
        if not self.rotating:
            return
        print("\nStopping...")
        self.rotating = False
        if self.rotation_thread:
            self.rotation_thread.join(timeout=1.0)
            self.rotation_thread = None
        # zero outputs
        self.set_field(0.0, 0.0, 0.0)

    # ---------------- Controller / SDL ----------------
    def poll_controller(self):
        if self.joystick is None:
            return  # no joystick present

        event = sdl2.SDL_Event()
        while sdl2.SDL_PollEvent(event):
            if event.type == sdl2.SDL_JOYBUTTONDOWN:
                btn = event.jbutton.button
                if btn == self.BTN_ROTATE:
                    if not self.rotating:
                        self.start_rotation()
                    else:
                        self.stop_rotation()

                elif btn == self.BTN_MODE:
                    modes = ["X", "Y", "Z", "XY", "XZ", "YZ"]
                    idx = modes.index(self.rotation_mode) if self.rotation_mode in modes else 0
                    self.rotation_mode = modes[(idx + 1) % len(modes)]
                    print(f"\nMode -> {self.rotation_mode}")

                elif btn == self.BTN_DIR:
                    self.direction *= -1
                    print(f"\nDirection -> {'CCW' if self.direction>0 else 'CW'}")

            elif event.type == sdl2.SDL_JOYAXISMOTION:
                # left stick Y axis adjust frequency
                if event.jaxis.axis == 1:
                    val = event.jaxis.value / 32767.0
                    self.rotation_freq = max(0.05, min(10.0, abs(val) * 10.0))
                    print(f"\rFreq: {self.rotation_freq:.2f} Hz", end="", flush=True)

            elif event.type == sdl2.SDL_QUIT:
                self.stop_rotation()
                self.cleanup()
                sys.exit()

    # ---------------- Cleanup ----------------
    def cleanup(self):
        self.stop_rotation()
        # stop all PWMs and set DIRs low
        for p in self.pwm.values():
            try:
                p.ChangeDutyCycle(0)
                p.stop()
            except Exception:
                pass

        for axis in ("X", "Y", "Z"):
            d1, d2 = self.dir_pins[axis]
            try:
                GPIO.output(d1, GPIO.LOW)
                GPIO.output(d2, GPIO.LOW)
            except Exception:
                pass

        GPIO.cleanup()
        try:
            sdl2.SDL_Quit()
        except Exception:
            pass


# ---------------- MAIN ----------------
if __name__ == "__main__":
    try:
        controller = MDD10A_DualCoilController()
        print("\nControls:")
        print(" A  -> toggle start/stop")
        print(" B  -> cycle mode (X -> Y -> Z -> XY -> XZ -> YZ)")
        print(" X  -> reverse direction (CW/CCW)")
        print(" Left stick Y -> adjust frequency\n")

        while True:
            controller.poll_controller()
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nKeyboard interrupt - cleaning up...")
        controller.cleanup()
        print("Exited cleanly.")
    except Exception as e:
        print("Error:", e)
        try:
            controller.cleanup()
        except Exception:
            pass
        raise
