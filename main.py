import sys
import cv2
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QDoubleSpinBox, QGridLayout, QHBoxLayout, QTabWidget
)

class PWMTab(QWidget):
    def __init__(self):
        super().__init__()
        self.coil_labels = ['x-coil', 'y-coil', 'z-coil']
        self.spin_boxes = {}

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(15)

        for i, label_text in enumerate(self.coil_labels):
            label = QLabel(label_text)
            spin_box = QDoubleSpinBox()
            spin_box.setRange(-1.00, 1.00)
            spin_box.setSingleStep(0.01)
            spin_box.setDecimals(2)
            spin_box.setValue(0.00)

            self.spin_boxes[label_text] = spin_box

            grid_layout.addWidget(label, i, 0)
            grid_layout.addWidget(spin_box, i, 1)
            grid_layout.setRowMinimumHeight(i, 40)

        layout.addLayout(grid_layout)

        button_layout = QHBoxLayout()
        reset_btn = QPushButton("Reset")
        submit_btn = QPushButton("Submit")

        reset_btn.clicked.connect(self.handle_button)
        submit_btn.clicked.connect(self.handle_button)

        button_layout.addWidget(reset_btn)
        button_layout.addWidget(submit_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def handle_button(self):
        sender = self.sender().text()
        if sender == "Reset":
            for spin_box in self.spin_boxes.values():
                spin_box.setValue(0.00)

        values = {label: spin_box.value() for label, spin_box in self.spin_boxes.items()}
        print(f"[{sender}] Values on PWM tab: {values}")

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
        layout = QVBoxLayout()
        label = QLabel("Movement controls and status will be implemented here.")
        label.setStyleSheet("font-size: 16px; padding: 20px;")
        layout.addWidget(label)
        layout.addStretch()
        self.setLayout(layout)

class CoilControlApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coil Control with Tabs")
        self.resize(640, 520)

        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.pwm_tab = PWMTab()
        self.camera_tab = CameraTab()
        self.movement_tab = MovementTab()

        self.tabs.addTab(self.pwm_tab, "PWM")
        self.tabs.addTab(self.camera_tab, "Camera")
        self.tabs.addTab(self.movement_tab, "Movement")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def closeEvent(self, event):
        # Ensure camera resource is released
        self.camera_tab.cap.release()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CoilControlApp()
    window.show()
    sys.exit(app.exec_())
