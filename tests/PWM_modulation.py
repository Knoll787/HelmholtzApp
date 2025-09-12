import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QDial, QHBoxLayout
)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
import time
from gpiozero import PWMOutputDevice, OutputDevice, Device
import math

# GPIO Mock as before (omitted here for brevity)...

class PWMControlApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AC PWM Simulator (Optimized PyQtGraph)")

        self.frequency = 1       # Hz
        self.amplitude = 1.0     # 0.0–1.0
        self.phase_deg = 0       # degrees
        self.resolution = 200    # samples per cycle

        layout = QVBoxLayout()
        self.function_label = QLabel("f(t) = sin(2πft + ϕ)")
        self.function_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.function_label)

        dial_layout = QHBoxLayout()
        self.freq_dial = self.create_dial("Freq (Hz)", 0, 70, 1, self.update_frequency)
        self.amp_dial = self.create_dial("Amplitude (%)", 0, 100, 100, self.update_amplitude)
        self.phase_dial = self.create_dial("Phase (°)", 0, 360, 0, self.update_phase)
        for _, dl in [self.freq_dial, self.amp_dial, self.phase_dial]:
            dial_layout.addLayout(dl)
        layout.addLayout(dial_layout)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setYRange(0, 100)
        self.plot_widget.setLabel('left', 'Duty Cycle (%)')
        self.plot_widget.setLabel('bottom', 'Time (s)')
        self.plot_widget.showGrid(x=True, y=True)
        layout.addWidget(self.plot_widget)

        self.pwm_curve = self.plot_widget.plot([], [], pen=pg.mkPen(color='b', width=2))

        self.setLayout(layout)

        # Precompute time vector for plotting, updated on frequency change
        self.t = np.linspace(0, 1 / self.frequency, self.resolution, endpoint=False)

        # Timer interval fixed to ~20ms for smooth UI but not too frequent
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_pwm)
        self.timer.start(20)

        self.start_time = time.time()

    def create_dial(self, label_text, min_val, max_val, default, callback):
        label = QLabel(f"{label_text}: {default}")
        dial = QDial()
        dial.setMinimum(min_val)
        dial.setMaximum(max_val)
        dial.setValue(default)
        dial.setNotchesVisible(True)
        dial.valueChanged.connect(lambda val: (label.setText(f"{label_text}: {val}"), callback(val)))

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(dial)
        return dial, layout

    def update_frequency(self, value):
        self.frequency = max(1, value)
        self.t = np.linspace(0, 1 / self.frequency, self.resolution, endpoint=False)
        self.plot_widget.setXRange(0, 1 / self.frequency)

    def update_amplitude(self, value):
        self.amplitude = value / 100.0

    def update_phase(self, value):
        self.phase_deg = value

    def update_pwm(self):
        elapsed = time.time() - self.start_time
        phase_rad = np.deg2rad(self.phase_deg)

        # Calculate full waveform for plotting
        signal = self.amplitude * np.sin(2 * np.pi * self.frequency * self.t + phase_rad)
        duty_cycle = 50 + 50 * signal

        self.function_label.setText(
            f"f(t) = {self.amplitude:.2f}·sin(2π·{self.frequency}·t + {self.phase_deg}°)"
        )

        # Update plot curve data
        self.pwm_curve.setData(self.t, duty_cycle)

        # For PWM output, calculate instantaneous duty cycle at current time
        current_signal = self.amplitude * np.sin(2 * np.pi * self.frequency * elapsed + phase_rad)
        current_dc = 50 + 50 * current_signal
        pwm.ChangeDutyCycle(current_dc)

    def closeEvent(self, event):
        pwm.stop()
        GPIO.cleanup()
        event.accept()


"""
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PWMControlApp()
    window.show()
    sys.exit(app.exec_())
"""

print("Coil Frequency (Hz)")
f_x = float(input("Frequency - X: "))
f_y = float(input("Frequency - Y: "))
f_z = float(input("Frequency - Z: "))

print("\nCoil Current (Amplitude: 0.0 to 1.0)")
i_x = float(input("Current - X: "))
i_y = float(input("Current - Y: "))
i_z = float(input("Current - Z: "))

print("\nCoil Phase (degrees)")
phi_x = float(input("Phase - X: "))
phi_y = float(input("Phase - Y: "))
phi_z = float(input("Phase - Z: "))

# Convert degrees to radians
phi_x = math.radians(phi_x)
phi_y = math.radians(phi_y)
phi_z = math.radians(phi_z)

# --- SETUP OUTPUT DEVICES ---

# Enable (PWM) Pins always ON
for pin in [12, 20, 5, 13, 17, 27]:
    OutputDevice(pin).on()

# Direction (PWM) Pins
DIR_Z1 = PWMOutputDevice(16)
DIR_Z2 = PWMOutputDevice(21)
DIR_Y3 = PWMOutputDevice(6)
DIR_Y4 = PWMOutputDevice(19)
DIR_X5 = PWMOutputDevice(22)
DIR_X6 = PWMOutputDevice(23)

# Initialize to 50% duty cycle (0 current)
for device in [DIR_Z1, DIR_Z2, DIR_Y3, DIR_Y4, DIR_X5, DIR_X6]:
    device.value = 0.5
    device.frequency = 5000

# --- PWM CONTROL LOOP ---
print("\nRunning PWM modulation. Press Ctrl+C to stop.\n")
try:
    start_time = time.time()
    while True:
        t = time.time() - start_time

        # Compute sinusoidal PWM values (centered at 0.5)
        pwm_x = 0.5 + i_x * math.sin(2 * math.pi * f_x * t + phi_x) / 2
        pwm_y = 0.5 + i_y * math.sin(2 * math.pi * f_y * t + phi_y) / 2
        pwm_z = 0.5 + i_z * math.sin(2 * math.pi * f_z * t + phi_z) / 2

        # Clamp values between 0 and 1 (safety)
        pwm_x = max(0.0, min(1.0, pwm_x))
        pwm_y = max(0.0, min(1.0, pwm_y))
        pwm_z = max(0.0, min(1.0, pwm_z))

        # Apply to both coils in each pair
        DIR_X5.value = pwm_x
        DIR_X6.value = pwm_x

        DIR_Y3.value = pwm_y
        DIR_Y4.value = pwm_y

        DIR_Z1.value = pwm_z
        DIR_Z2.value = pwm_z

        time.sleep(0.001)  # 100 Hz update rate

except KeyboardInterrupt:
    print("\nPWM modulation stopped.")

    # Reset to 50% (0 current)
    for device in [DIR_Z1, DIR_Z2, DIR_Y3, DIR_Y4, DIR_X5, DIR_X6]:
        device.value = 0.5
