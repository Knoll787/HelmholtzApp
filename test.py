from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QSlider, QPushButton, QComboBox, QFrame
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
        self.setGeometry(100, 100, 350, 750)
        
        layout = QVBoxLayout()

        # ======== X-Axis Section ========
        layout.addWidget(self.make_divider("X-Axis Control"))

        self.x_mode = QComboBox()
        self.x_mode.addItems(["Helmholtz", "Maxwell", "Gradient"])
        self.x_mode.currentIndexChanged.connect(self.toggle_extra_sliders)
        layout.addWidget(QLabel("X Coil Mode"))
        layout.addWidget(self.x_mode)

        self.slider1 = self.make_slider(layout, "Main X Slider")
        self.label1 = QLabel("0.00")
        layout.addWidget(self.label1)

        self.x_grad_slider1 = self.make_slider(layout, "X Coil 1")
        self.x_grad_slider2 = self.make_slider(layout, "X Coil 2")

        # ======== Y-Axis Section ========
        layout.addWidget(self.make_divider("Y-Axis Control"))

        self.y_mode = QComboBox()
        self.y_mode.addItems(["Helmholtz", "Maxwell", "Gradient"])
        self.y_mode.currentIndexChanged.connect(self.toggle_extra_sliders)
        layout.addWidget(QLabel("Y Coil Mode"))
        layout.addWidget(self.y_mode)

        self.slider2 = self.make_slider(layout, "Main Y Slider")
        self.label2 = QLabel("0.00")
        layout.addWidget(self.label2)

        self.y_grad_slider1 = self.make_slider(layout, "Y Coil 1")
        self.y_grad_slider2 = self.make_slider(layout, "Y Coil 2")

        # ======== Z-Axis Section ========
        layout.addWidget(self.make_divider("Z-Axis Control"))

        self.z_mode = QComboBox()
        self.z_mode.addItems(["Helmholtz", "Maxwell", "Gradient"])
        self.z_mode.currentIndexChanged.connect(self.toggle_extra_sliders)
        layout.addWidget(QLabel("Z Coil Mode"))
        layout.addWidget(self.z_mode)

        self.slider3 = self.make_slider(layout, "Main Z Slider")
        self.label3 = QLabel("0.00")
        layout.addWidget(self.label3)

        self.z_grad_slider1 = self.make_slider(layout, "Z Coil 1")
        self.z_grad_slider2 = self.make_slider(layout, "Z Coil 2")

        # ======== Buttons Section ========
        layout.addWidget(self.make_divider("Controls"))

        self.update_button = QPushButton("Update State")
        self.update_button.clicked.connect(self.update_state)
        layout.addWidget(self.update_button)

        self.reset_button = QPushButton("Reset State")
        self.reset_button.clicked.connect(self.reset_state)
        layout.addWidget(self.reset_button)

        self.setLayout(layout)
        self.toggle_extra_sliders()

    def make_slider(self, layout, label_text):
        layout.addWidget(QLabel(label_text))
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(-100)
        slider.setMaximum(100)
        slider.setValue(0)
        slider.valueChanged.connect(self.update_labels)
        layout.addWidget(slider)
        return slider

    def make_divider(self, text):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.HLine)
        frame.setFrameShadow(QFrame.Shadow.Sunken)
        label = QLabel(f"--- {text} ---")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container = QVBoxLayout()
        container.addWidget(label)
        container.addWidget(frame)
        div = QWidget()
        div.setLayout(container)
        return div

    def toggle_extra_sliders(self):
        # Enable/disable gradient sliders instead of hiding
        self.x_grad_slider1.setEnabled(self.x_mode.currentText() == "Gradient")
        self.x_grad_slider2.setEnabled(self.x_mode.currentText() == "Gradient")
        self.slider1.setEnabled(self.x_mode.currentText() != "Gradient")

        self.y_grad_slider1.setEnabled(self.y_mode.currentText() == "Gradient")
        self.y_grad_slider2.setEnabled(self.y_mode.currentText() == "Gradient")
        self.slider2.setEnabled(self.y_mode.currentText() != "Gradient")

        self.z_grad_slider1.setEnabled(self.z_mode.currentText() == "Gradient")
        self.z_grad_slider2.setEnabled(self.z_mode.currentText() == "Gradient")
        self.slider3.setEnabled(self.z_mode.currentText() != "Gradient")

    def update_labels(self):
        self.label1.setText(f"{self.slider1.value() / 100:.2f}")
        self.label2.setText(f"{self.slider2.value() / 100:.2f}")
        self.label3.setText(f"{self.slider3.value() / 100:.2f}")

    def update_state(self):
        # Z-axis
        if self.z_mode.currentText() == "Gradient":
            valz1 = self.z_grad_slider1.value() / 100
            valz2 = self.z_grad_slider2.value() / 100
            set_coil(coil1_pwm, coil1_dir, abs(valz1), valz1 >= 0)
            set_coil(coil2_pwm, coil2_dir, abs(valz2), valz2 >= 0)
        else:
            valz = self.slider3.value() / 100
            dir_z = valz >= 0
            set_coil(coil1_pwm, coil1_dir, abs(valz), dir_z)
            set_coil(coil2_pwm, coil2_dir, abs(valz),
                     dir_z if self.z_mode.currentText() == "Helmholtz" else not dir_z)

        # Y-axis
        if self.y_mode.currentText() == "Gradient":
            valy1 = self.y_grad_slider1.value() / 100
            valy2 = self.y_grad_slider2.value() / 100
            set_coil(coil3_pwm, coil3_dir, abs(valy1), valy1 >= 0)
            set_coil(coil4_pwm, coil4_dir, abs(valy2), valy2 >= 0)
        else:
            valy = self.slider2.value() / 100
            dir_y = valy >= 0
            set_coil(coil3_pwm, coil3_dir, abs(valy), dir_y)
            set_coil(coil4_pwm, coil4_dir, abs(valy),
                     dir_y if self.y_mode.currentText() == "Helmholtz" else not dir_y)

        # X-axis
        if self.x_mode.currentText() == "Gradient":
            valx1 = self.x_grad_slider1.value() / 100
            valx2 = self.x_grad_slider2.value() / 100
            set_coil(coil5_pwm, coil5_dir, abs(valx1), valx1 >= 0)
            set_coil(coil6_pwm, coil6_dir, abs(valx2), valx2 >= 0)
        else:
            valx = self.slider1.value() / 100
            dir_x = valx >= 0
            set_coil(coil5_pwm, coil5_dir, abs(valx), dir_x)
            set_coil(coil6_pwm, coil6_dir, abs(valx),
                     dir_x if self.x_mode.currentText() == "Helmholtz" else not dir_x)

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
        self.x_grad_slider1.setValue(0)
        self.x_grad_slider2.setValue(0)
        self.y_grad_slider1.setValue(0)
        self.y_grad_slider2.setValue(0)
        self.z_grad_slider1.setValue(0)
        self.z_grad_slider2.setValue(0)

        self.update_labels()
        print("Slider Values: 0.00, 0.00, 0.00")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MotorControlGUI()
    window.show()
    sys.exit(app.exec())
