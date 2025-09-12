from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QComboBox, QFrame
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
# Z - Coils
PWM_PIN1, DIR_PIN1 = 12, 16 # Motor A
PWM_PIN2, DIR_PIN2 = 20, 21 # Motor B

# Y - Coils
PWM_PIN3, DIR_PIN3 = 5, 6   # Motor A
PWM_PIN4, DIR_PIN4 = 13, 19 # Motor B

# Z - Coils
PWM_PIN5, DIR_PIN5 = 17, 22 # Motor A
PWM_PIN6, DIR_PIN6 = 27, 23 # Motor B

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
        self.setGeometry(100, 100, 900, 500)
        
        main_layout = QVBoxLayout()  # Overall layout
        controls_layout = QHBoxLayout()  # Horizontal layout for X, Y, Z

        # ======== X-Axis Column ========
        x_layout = QVBoxLayout()
        x_layout.addWidget(self.make_divider("X Axis"))

        self.x_mode = QComboBox()
        self.x_mode.addItems(["Helmholtz", "Maxwell", "Gradient"])
        self.x_mode.currentIndexChanged.connect(self.toggle_extra_sliders)
        x_layout.addWidget(QLabel("X Coil Mode"))
        x_layout.addWidget(self.x_mode)

        self.slider1, self.label1 = self.make_slider_with_label(x_layout, "Main X Slider")
        self.x_grad_slider1, self.x_grad_label1 = self.make_slider_with_label(x_layout, "X Coil 1")
        self.x_grad_slider2, self.x_grad_label2 = self.make_slider_with_label(x_layout, "X Coil 2")

        controls_layout.addLayout(x_layout)

        # ======== Y-Axis Column ========
        y_layout = QVBoxLayout()
        y_layout.addWidget(self.make_divider("Y Axis"))

        self.y_mode = QComboBox()
        self.y_mode.addItems(["Helmholtz", "Maxwell", "Gradient"])
        self.y_mode.currentIndexChanged.connect(self.toggle_extra_sliders)
        y_layout.addWidget(QLabel("Y Coil Mode"))
        y_layout.addWidget(self.y_mode)

        self.slider2, self.label2 = self.make_slider_with_label(y_layout, "Main Y Slider")
        self.y_grad_slider1, self.y_grad_label1 = self.make_slider_with_label(y_layout, "Y Coil 1")
        self.y_grad_slider2, self.y_grad_label2 = self.make_slider_with_label(y_layout, "Y Coil 2")

        controls_layout.addLayout(y_layout)

        # ======== Z-Axis Column ========
        z_layout = QVBoxLayout()
        z_layout.addWidget(self.make_divider("Z Axis"))

        self.z_mode = QComboBox()
        self.z_mode.addItems(["Helmholtz", "Maxwell", "Gradient"])
        self.z_mode.currentIndexChanged.connect(self.toggle_extra_sliders)
        z_layout.addWidget(QLabel("Z Coil Mode"))
        z_layout.addWidget(self.z_mode)

        self.slider3, self.label3 = self.make_slider_with_label(z_layout, "Main Z Slider")
        self.z_grad_slider1, self.z_grad_label1 = self.make_slider_with_label(z_layout, "Z Coil 1")
        self.z_grad_slider2, self.z_grad_label2 = self.make_slider_with_label(z_layout, "Z Coil 2")

        controls_layout.addLayout(z_layout)

        # Add controls row to main layout
        main_layout.addLayout(controls_layout)

        # ======== Buttons Section ========
        main_layout.addWidget(self.make_divider("Controls"))
        self.update_button = QPushButton("Update State")
        self.update_button.clicked.connect(self.update_state)
        main_layout.addWidget(self.update_button)

        self.reset_button = QPushButton("Reset State")
        self.reset_button.clicked.connect(self.reset_state)
        main_layout.addWidget(self.reset_button)

        self.setLayout(main_layout)
        self.toggle_extra_sliders()

    def make_slider_with_label(self, layout, label_text):
        layout.addWidget(QLabel(label_text))
        slider_row = QHBoxLayout()
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(-100)
        slider.setMaximum(100)
        slider.setValue(0)
        value_label = QLabel("0.00")
        value_label.setFixedWidth(50)
        slider.valueChanged.connect(lambda: value_label.setText(f"{slider.value()/100:.2f}"))
        slider_row.addWidget(slider)
        slider_row.addWidget(value_label)
        layout.addLayout(slider_row)
        return slider, value_label

    def make_divider(self, text):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.HLine)
        frame.setFrameShadow(QFrame.Shadow.Sunken)
        label = QLabel(f"{text}")
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

        print("Slider Values: 0.00, 0.00, 0.00")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MotorControlGUI()
    window.show()
    sys.exit(app.exec())
f