"""
import sys
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QDoubleSpinBox, QGridLayout, QHBoxLayout, QTabWidget, QComboBox, QTableWidget, QTableWidgetItem, QDial
)
from PyQt5.QtSvg import (QSvgWidget, QSvgRenderer) 
from hardware import coils
import numpy as np



class yolo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App")
        self.resize(640, 520)

        layout = QGridLayout()

        A_label = QLabel("A")
        omega_label = QLabel("x")
        phi_label = QLabel("phi")
        
        A_dial = QDial()
        omega_dial = QDial()
        phi_dial = QDial()
        A_dial.setFixedSize(40,40)
        omega_dial.setFixedSize(40,40)
        phi_dial.setFixedSize(40,40)
        
        layout.addWidget(A_label, 0, 0)
        layout.addWidget(omega_label, 1, 0)
        layout.addWidget(phi_label, 2, 0)

        layout.addWidget(A_dial, 0, 1)
        layout.addWidget(omega_dial, 1, 1)
        layout.addWidget(phi_dial, 2, 1)
        
        

        
        self.setLayout(layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = yolo()
    window.show()
    sys.exit(app.exec_())
"""


import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QDial, QHBoxLayout
)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
import time

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PWMControlApp()
    window.show()
    sys.exit(app.exec_())
