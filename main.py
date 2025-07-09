import sys
import cv2
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QDoubleSpinBox, QGridLayout, QHBoxLayout, QTabWidget, QComboBox, QTableWidget, QTableWidgetItem
)
from PyQt5.QtSvg import (QSvgWidget, QSvgRenderer) 
from hardware import coils
import numpy as np

class CameraTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.video_label = QLabel("Camera feed loading...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.video_label)
        self.setLayout(self.layout)

        # Start video capture
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.video_label.setText("Failed to access webcam")
            return

        # Set frame size if desired
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Start timer for updating frame (15 FPS => ~66ms interval)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(66)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qt_image)
            self.video_label.setPixmap(pix)
        else:
            self.video_label.setText("Failed to read frame")

    def closeEvent(self, event):
        self.cap.release()
        event.accept()


class MovementTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control Mode Selector")

        # Create label and combo box
        self.label = QLabel("Control Mode:")
        self.combo_box = QComboBox()
        self.combo_box.addItems([
            "Field Alignment",
            "Rolling",
            "Tumbling",
            "Path Following"
        ])
        self.combo_box.currentTextChanged.connect(self.on_mode_changed)

        # Top row layout for label and combo box
        top_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()
        top_layout.addWidget(self.label)
        top_layout.addWidget(self.combo_box)
        top_layout.addStretch()

        # Layout where dynamic content will be placed
        self.dynamic_layout = QVBoxLayout()
        
        # Layout for the current system state
        self.current_values = []
        self.pwm_values = []
        self.field_values = []
        self.param_layout = QGridLayout()
        self.load_params() 
        
        # Action Buttons
        btn_submit = QPushButton("Sumbit")
        btn_reset= QPushButton("Reset")
        btn_submit.clicked.connect(self.btn_submit_action)
        btn_reset.clicked.connect(self.btn_reset_action)
        bottom_layout.addWidget(btn_submit)
        bottom_layout.addWidget(btn_reset)


        # Overall layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addLayout(self.dynamic_layout)
        main_layout.addLayout(self.param_layout)
        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

        # Load initial mode
        self.on_mode_changed(self.combo_box.currentText())

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def btn_submit_action(self):
        mode = self.combo_box.currentText()
        if mode == "Field Alignment":
            # Field Strength
            b = [self.bx_spin.value(), self.bx_spin.value(),
                 self.by_spin.value(), self.by_spin.value(),
                 self.bz_spin.value(), self.bz_spin.value()]

            self.x= coils.field_to_pwm(np.array(b))
            self.y= coils.field_to_current(np.array(b))
            self.update_params()


        elif mode == "Rolling":
            print(mode)
            # Do Stuff here
        elif mode == "Tumbling":
            print(mode)
            # Do Stuff here
        elif mode == "Path Following":
            print(mode)
            # Do Stuff here

    def btn_reset_action(self):
        mode = self.combo_box.currentText()
        if mode == "Field Alignment":
            print(mode)
            # Do Stuff here
        elif mode == "Rolling":
            print(mode)
            # Do Stuff here
        elif mode == "Tumbling":
            print(mode)
            # Do Stuff here
        elif mode == "Path Following":
            print(mode)
            # Do Stuff here

    def on_mode_changed(self, mode):
        self.clear_layout(self.dynamic_layout)

        if mode == "Field Alignment":
            self.load_field_alignment_ui()
        elif mode == "Rolling":
            self.load_rolling_ui()
        elif mode == "Tumbling":
            self.load_tumbling_ui()
        elif mode == "Path Following":
            self.load_path_following_ui()

    def load_field_alignment_ui(self):
        # Label
        label = QLabel("Desired Field")
        self.dynamic_layout.addWidget(label)

        # Spin boxes for Bx, By, Bz
        field_layout = QGridLayout()
        bx_label = QLabel("Bx [mT]:")
        by_label = QLabel("By [mT]:")
        bz_label = QLabel("Bz [mT]:")
        self.bx_spin = QDoubleSpinBox()
        self.by_spin = QDoubleSpinBox()
        self.bz_spin = QDoubleSpinBox()
        field_layout.addWidget(bx_label, 0, 0)
        field_layout.addWidget(self.bx_spin, 0, 1)
        field_layout.addWidget(by_label, 1, 0)
        field_layout.addWidget(self.by_spin, 1, 1)
        field_layout.addWidget(bz_label, 2, 0)
        field_layout.addWidget(self.bz_spin, 2, 1)

        self.dynamic_layout.addLayout(field_layout)

        # Spacer
        self.dynamic_layout.addStretch()


    def load_params(self):
        self.param_layout.addWidget(QLabel("<b>Current (A)</b>"), 0, 0, alignment=Qt.AlignCenter)
        self.param_layout.addWidget(QLabel("<b>PWM (Duty Cycle)</b>"), 0, 1, alignment=Qt.AlignCenter)

        # Create label holders for 6 values each
        self.current_values = []
        self.pwm_values = []

        for i in range(6):
            current_label = QLabel("0.0 A")
            pwm_label = QLabel("0.0 %")

            current_label.setAlignment(Qt.AlignCenter)
            pwm_label.setAlignment(Qt.AlignCenter)

            self.current_values.append(current_label)
            self.pwm_values.append(pwm_label)

            self.param_layout.addWidget(current_label, i + 1, 0)
            self.param_layout.addWidget(pwm_label, i + 1, 1)


        
    def update_params(self):
        for i in range(6):
            current_value = self.x[i]
            pwm_value = self.y[i] 

            self.current_values[i].setText(f"{current_value:.2f}")
            self.pwm_values[i].setText(f"{pwm_value:.2f}%")



    def load_rolling_ui(self):
        field_layout = QGridLayout()

        label = QLabel("Field Characteristic")
        field_layout.addWidget(label, 0, 0)

        b0_label = QLabel("B0 [mT]:")
        omega_label = QLabel("ω [rad/s]:")
        self.b0_spin = QDoubleSpinBox()
        self.omega_spin = QDoubleSpinBox()
        field_layout.addWidget(b0_label, 3, 0)
        field_layout.addWidget(self.b0_spin, 3, 1)
        field_layout.addWidget(omega_label, 5, 0)
        field_layout.addWidget(self.omega_spin, 5, 1)

        # SVG Handleing 
        svg_widget = QSvgWidget()
        svg_widget.load("resources/equations/rolling.svg")  # Replace with your SVG file path
        renderer = QSvgRenderer("resources/equations/rolling.svg")
        orig_size = renderer.defaultSize()
        factor = 0.8
        scaled_width = int(orig_size.width() * factor)
        scaled_height = int(orig_size.height() * factor)
        svg_widget.setFixedSize(scaled_width, scaled_height)
        field_layout.addWidget(svg_widget, 0, 1)

        self.dynamic_layout.addLayout(field_layout)

        # Spacer
        self.dynamic_layout.addStretch()
        


    def load_tumbling_ui(self):
        field_layout = QGridLayout()

        label = QLabel("Field Characteristic")
        field_layout.addWidget(label, 0, 0)

        b0_label = QLabel("B0 [mT]:")
        omega_label = QLabel("ω [rad/s]:")
        self.b0_spin = QDoubleSpinBox()
        self.omega_spin = QDoubleSpinBox()
        field_layout.addWidget(b0_label, 3, 0)
        field_layout.addWidget(self.b0_spin, 3, 1)
        field_layout.addWidget(omega_label, 5, 0)
        field_layout.addWidget(self.omega_spin, 5, 1)

        # SVG Handleing 
        svg_widget = QSvgWidget()
        svg_widget.load("resources/equations/tumbling.svg")  # Replace with your SVG file path
        renderer = QSvgRenderer("resources/equations/tumbling.svg")
        orig_size = renderer.defaultSize()
        factor = 0.8
        scaled_width = int(orig_size.width() * factor)
        scaled_height = int(orig_size.height() * factor)
        svg_widget.setFixedSize(scaled_width, scaled_height)
        field_layout.addWidget(svg_widget, 0, 1)

        self.dynamic_layout.addLayout(field_layout)

        # Spacer
        self.dynamic_layout.addStretch()
        

    def load_path_following_ui(self):
        label = QLabel("Path Following mode is under development.")
        self.dynamic_layout.addWidget(label)


class HelmholtzApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coil Control with Tabs")
        self.resize(640, 520)

        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.movement_tab = MovementTab()
        self.camera_tab = CameraTab()

        self.tabs.addTab(self.movement_tab, "Movement")
        self.tabs.addTab(self.camera_tab, "Camera")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def closeEvent(self, event):
        # Ensure camera resource is released
        self.camera_tab.cap.release()
        event.accept()


if __name__ == '__main__':
    #hardware = coils.Coils()
    app = QApplication(sys.argv)
    window = HelmholtzApp()
    window.show()
    sys.exit(app.exec_())
