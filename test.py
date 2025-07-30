from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QSlider, QPushButton, QComboBox
)
from PyQt6.QtCore import Qt
import sys
import platform

# Detect platform
is_rpi = platform.system() == "Linux"

# GPIO Setup or Mock
if is_rpi:
    from gpiozero import PWMOutputDevice, OutputDevice
else:
    print("Running in development mode (GPIO mocked)")

    class PWMOutputDevice:
        def __init__(self, pin, frequency=1000):
            self.pin = pin
            self.frequency = frequency
            self.value = 0.0
        def __repr__(self):
            return f"MockPWM(pin={self.pin}, freq={self.frequency}, value={self.value})"

    class OutputDevice:
        def __init__(self, pin):
            self.pin = pin
            self.active = False
        def on(self):
            self.active = True
        def off(self):
            self.active = False
        @property
        def is_active(self):
            return self.active
        def __repr__(self):
            return f"MockOutput(pin={self.pin}, active={self.active})"

# GPIO pins
PWM_PIN1, DIR_PIN1 = 12, 16
PWM_PIN2, DIR_PIN2 = 20, 21
PWM_PIN3, DIR_PIN3 = 5, 6
PWM_PIN4, DIR_PIN4 = 13, 19
PWM_PIN5, DIR_PIN5 = 17, 22
PWM_PIN6, DIR_PIN6 = 27, 23

coil1_pwm = PWMOutputDevice(PWM_PIN1, frequency=1000)
coil1_dir = OutputDevice(DIR_PIN1)
coil2_pwm = PWMOutputDevice(PWM_PIN2, frequency=1000)
coil2_dir = OutputDevice(DIR_PIN2)
coil3_pwm = PWMOutputDevice(PWM_PIN3, frequency=1000)
coil3_dir = OutputDevice(DIR_PIN3)
coil4_pwm = PWMOutputDevice(PWM_PIN4, frequency=1000)
coil4_dir = OutputDevice(DIR_PIN4)
coil5_pwm = PWMOutputDevice(PWM_PIN5, frequency=1000)
coil5_dir = OutputDevice(DIR_PIN5)
coil6_pwm = PWMOutputDevice(PWM_PIN6, frequency=1000)
coil6_dir = OutputDevice(DIR_PIN6)

def set_coil(coil_pwm, coil_dir, power, direction):
    coil_dir.on() if direction else coil_dir.off()
    coil_pwm.value = power
    print(f"Set {coil_dir} with power {power:.2f}, direction {'on' if direction else 'off'}")

class MotorControlGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Slider Control")
        self.setGeometry(100, 100, 300, 500)
        
        layout = QVBoxLayout()

        # ========== X-Axis ==========
        self.x_label = QLabel("X-Axis")
        layout.addWidget(self.x_label)

        self.slider1 = QSlider(Qt.Orientation.Horizontal)
        self.slider1.setMinimum(-100)
        self.slider1.setMaximum(100)
        self.slider1.setValue(0)
        self.slider1.valueChanged.connect(self.update_labels)
        layout.addWidget(self.slider1)

        self.label1 = QLabel("0.00")
        layout.addWidget(self.label1)

        self.x_mode = QComboBox()
        self.x_mode.addItems(["Helmholtz", "Maxwell"])
        layout.addWidget(QLabel("X Coil Mode"))
        layout.addWidget(self.x_mode)

        # ========== Y-Axis ==========
        self.y_label = QLabel("Y-Axis")
        layout.addWidget(self.y_label)

        self.slider2 = QSlider(Qt.Orientation.Horizontal)
        self.slider2.setMinimum(-100)
        self.slider2.setMaximum(100)
        self.slider2.setValue(0)
        self.slider2.valueChanged.connect(self.update_labels)
        layout.addWidget(self.slider2)

        self.label2 = QLabel("0.00")
        layout.addWidget(self.label2)

        self.y_mode = QComboBox()
        self.y_mode.addItems(["Helmholtz", "Maxwell"])
        layout.addWidget(QLabel("Y Coil Mode"))
        layout.addWidget(self.y_mode)

        # ========== Z-Axis ==========
        self.z_label = QLabel("Z-Axis")
        layout.addWidget(self.z_label)

        self.slider3 = QSlider(Qt.Orientation.Horizontal)
        self.slider3.setMinimum(-100)
        self.slider3.setMaximum(100)
        self.slider3.setValue(0)
        self.slider3.valueChanged.connect(self.update_labels)
        layout.addWidget(self.slider3)

        self.label3 = QLabel("0.00")
        layout.addWidget(self.label3)

        self.z_mode = QComboBox()
        self.z_mode.addItems(["Helmholtz", "Maxwell"])
        layout.addWidget(QLabel("Z Coil Mode"))
        layout.addWidget(self.z_mode)

        # ========== Buttons ==========
        self.update_button = QPushButton("Update State")
        self.update_button.clicked.connect(self.update_state)
        layout.addWidget(self.update_button)

        self.reset_button = QPushButton("Reset State")
        self.reset_button.clicked.connect(self.reset_state)
        layout.addWidget(self.reset_button)

        self.setLayout(layout)

    def update_labels(self):
        self.label1.setText(f"{self.slider1.value() / 100:.2f}")
        self.label2.setText(f"{self.slider2.value() / 100:.2f}")
        self.label3.setText(f"{self.slider3.value() / 100:.2f}")

    def update_state(self):
        valx = self.slider1.value() / 100
        valy = self.slider2.value() / 100
        valz = self.slider3.value() / 100

        dir_x = valx >= 0
        dir_y = valy >= 0
        dir_z = valz >= 0

        mode_x = self.x_mode.currentText()
        mode_y = self.y_mode.currentText()
        mode_z = self.z_mode.currentText()

        # Apply mode logic
        # Helmholtz: both coils same direction
        # Maxwell: coils opposite directions

        # Z-Coils
        set_coil(coil1_pwm, coil1_dir, abs(valz), dir_z)
        set_coil(coil2_pwm, coil2_dir, abs(valz),
                 dir_z if mode_z == "Helmholtz" else not dir_z)

        # Y-Coils
        set_coil(coil3_pwm, coil3_dir, abs(valy), dir_y)
        set_coil(coil4_pwm, coil4_dir, abs(valy),
                 dir_y if mode_y == "Helmholtz" else not dir_y)

        # X-Coils
        set_coil(coil5_pwm, coil5_dir, abs(valx), dir_x)
        set_coil(coil6_pwm, coil6_dir, abs(valx),
                 dir_x if mode_x == "Helmholtz" else not dir_x)

        print(f"Slider Values: {valx:.2f}, {valy:.2f}, {valz:.2f}")
        print(f"Modes: X={mode_x}, Y={mode_y}, Z={mode_z}")

    def reset_state(self):
        for coil_pwm, coil_dir in [
            (coil1_pwm, coil1_dir),
            (coil2_pwm, coil2_dir),
            (coil3_pwm, coil3_dir),
            (coil4_pwm, coil4_dir),
            (coil5_pwm, coil5_dir),
            (coil6_pwm, coil6_dir),
        ]:
            set_coil(coil_pwm, coil_dir, 0.0, True)

        self.slider1.setValue(0)
        self.slider2.setValue(0)
        self.slider3.setValue(0)

        self.update_labels()
        print("Slider Values: 0.00, 0.00, 0.00")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MotorControlGUI()
    window.show()
    sys.exit(app.exec())
