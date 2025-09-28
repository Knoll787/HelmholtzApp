import sys
import cv2
import numpy as np
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QLabel, QMainWindow, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QTextEdit
)

import image_processing as ip
import movement as mv
import controllers as ctlr


class CameraWidget(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Tracking GUI")
        self.resize(500, 500)

        # Camera
        self.camera = ip.PiCamera()
        ret, first_frame = self.camera.read()
        if not ret:
            raise RuntimeError("Could not read first frame from PiCamera")

        # ROI selection variables
        self.roi_points = []
        self.roi_mask = None
        self.selecting_roi = True

        # Target point
        self.target = None

        # --- Video feed as main focus ---
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.mousePressEvent = self.on_mouse_click

        # --- Controls and info below video ---
        self.toggle_button = QPushButton("Show Mask")
        self.toggle_button.clicked.connect(self.toggle_view)

        self.position_text = QTextEdit()
        self.position_text.setReadOnly(True)
        self.position_text.setFixedHeight(50)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.toggle_button)
        bottom_layout.addWidget(QLabel("Position:"))
        bottom_layout.addWidget(self.position_text)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.video_label, stretch=1)
        main_layout.addLayout(bottom_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # State
        self.show_mask = False
        self.pos = None

        # Movement + controllers
        self.x_coil = mv.Coil(FWD=17, BWD=27)
        self.y_coil = mv.Coil(FWD=13, BWD=5)
        self.ctl_x = None
        self.ctl_y = None

    def toggle_view(self):
        self.show_mask = not self.show_mask
        self.toggle_button.setText("Show Camera Feed" if self.show_mask else "Show Mask")

    def update_frame(self):
        ret, frame = self.camera.read()
        if not ret:
            return

        if self.roi_mask is None:
            # ROI selection phase
            tmp = frame.copy()
            for p in self.roi_points:
                cv2.circle(tmp, p, 6, (0, 0, 255), -1)
            if len(self.roi_points) >= 2:
                cv2.polylines(tmp, [np.array(self.roi_points, dtype=np.int32)], isClosed=False, color=(0, 255, 255), thickness=1)
            self.display_frame(tmp)
            return

        # Once ROI is set, track
        comp_mask = ip.mask(frame, roi_points=self.roi_points)
        self.pos = ip.track(comp_mask, min_area=500)

        if self.pos is not None:
            if self.target is not None:
                cv2.circle(frame, self.target, radius=5, color=(0, 0, 255), thickness=2)
            cv2.circle(frame, self.pos, radius=5, color=(255, 0, 0), thickness=2)
            self.position_text.setText(f"x: {self.pos[0]}, y: {self.pos[1]}")
        else:
            self.position_text.setText("No object found")

        if self.show_mask:
            self.display_frame(comp_mask, is_mask=True)
        else:
            self.display_frame(frame)

    def display_frame(self, frame, is_mask=False):
        if is_mask:
            qimg = QImage(frame.data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format.Format_Grayscale8)
        else:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            qimg = QImage(rgb_image.data, rgb_image.shape[1], rgb_image.shape[0], rgb_image.strides[0], QImage.Format.Format_RGB888)

        self.video_label.setPixmap(QPixmap.fromImage(qimg).scaled(
            self.video_label.width(), self.video_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio
        ))

    def on_mouse_click(self, event):
        if self.roi_mask is None:
            # Collect ROI points
            if len(self.roi_points) < 4:
                self.roi_points.append((event.pos().x(), event.pos().y()))
                if len(self.roi_points) == 4:
                    self.roi_mask = np.zeros((640, 640), dtype=np.uint8)
                    cv2.fillPoly(self.roi_mask, [np.array(self.roi_points, dtype=np.int32)], 255)
                    print("ROI set.")
        else:
            # Set target point if within ROI
            x, y = event.pos().x(), event.pos().y()
            if 0 <= y < self.roi_mask.shape[0] and 0 <= x < self.roi_mask.shape[1] and self.roi_mask[y, x] > 0:
                self.target = (x, y)
                print(f"New target set: {self.target}")
                if self.ctl_x is None or self.ctl_y is None:
                    self.ctl_x = ctlr.PID("x", kp=1.00, ki=0.10, kd=0.00, setpoint=self.target[0], output_limits=(-100, 100))
                    self.ctl_y = ctlr.PID("y", kp=1.00, ki=0.10, kd=0.00, setpoint=self.target[1], output_limits=(-100, 100))
            else:
                print("Click ignored: outside ROI")

    def closeEvent(self, event):
        self.camera.release()
        self.x_coil.cleanup()
        self.y_coil.cleanup()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = CameraWidget()
    win.show()
    sys.exit(app.exec())