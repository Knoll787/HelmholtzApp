import sys
import cv2
import numpy as np
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QLabel, QMainWindow, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget
)

import image_processing as ip
import movement as mv
import controllers as ctlr


class CameraWidget(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window fixed to 500x500
        self.setWindowTitle("Tracking GUI")
        self.setFixedSize(500, 500)

        # Camera
        self.camera = ip.PiCamera()
        ret, first_frame = self.camera.read()
        if not ret:
            raise RuntimeError("Could not read first frame from PiCamera")

        self._frame_size = (first_frame.shape[1], first_frame.shape[0])  # (width, height)

        # ROI + Target
        self.roi_points = []
        self.roi_mask = None
        self.target = None
        self.select_target_mode = False
        self.show_pos_cursor = True

        # --- Video feed as main focus ---
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.mousePressEvent = self.on_mouse_click

        # --- Controls and info ---
        self.toggle_button = QPushButton("Show Mask")
        self.toggle_button.clicked.connect(self.toggle_view)

        self.toggle_target_button = QPushButton("Select Target")
        self.toggle_target_button.setCheckable(True)
        self.toggle_target_button.clicked.connect(self.toggle_target_mode)

        self.cursor_button = QPushButton("Hide Cursor")
        self.cursor_button.setCheckable(True)
        self.cursor_button.clicked.connect(self.toggle_cursor)

        self.position_label = QLabel("Position: -,-")
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position_label.setFixedWidth(130)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.toggle_button)
        bottom_layout.addWidget(self.toggle_target_button)
        bottom_layout.addWidget(self.cursor_button)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.position_label)

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

        # State used for mapping clicks
        self._pixmap_size = (0, 0)
        self._label_size = (self.video_label.width(), self.video_label.height())

        # Movement + controllers
        self.x_coil = mv.Coil(FWD=17, BWD=27)
        self.y_coil = mv.Coil(FWD=13, BWD=5)
        self.ctl_x = None
        self.ctl_y = None

    # --- UI control callbacks ---
    def toggle_view(self):
        self.show_mask = not getattr(self, 'show_mask', False)
        self.toggle_button.setText("Show Camera Feed" if self.show_mask else "Show Mask")

    def toggle_target_mode(self):
        self.select_target_mode = self.toggle_target_button.isChecked()
        self.toggle_target_button.setText("Cancel Target Select" if self.select_target_mode else "Select Target")

    def toggle_cursor(self):
        self.show_pos_cursor = not self.cursor_button.isChecked()
        self.cursor_button.setText("Hide Cursor" if self.show_pos_cursor else "Show Cursor")

    # --- Main loop ---
    def update_frame(self):
        ret, frame = self.camera.read()
        if not ret:
            return

        self._frame_size = self.camera.get_frame_size()
        display_frame = frame.copy()

        if self.roi_mask is None:
            for p in self.roi_points:
                cv2.circle(display_frame, p, 6, (0, 0, 255), -1)
            if len(self.roi_points) >= 2:
                cv2.polylines(display_frame, [np.array(self.roi_points, dtype=np.int32)],
                              isClosed=False, color=(0, 255, 255), thickness=1)
            self.display_frame(display_frame)
            return

        # Mask + tracking
        comp_mask = ip.mask(frame, roi_points=self.roi_points)
        pos = ip.track(comp_mask, min_area=500)
        self.pos = pos

        if pos is not None:
            if self.target is not None:
                cv2.circle(display_frame, self.target, radius=6, color=(0, 0, 255), thickness=2)
                error = ip.calculate_error(pos, self.target)
                if error:
                    print(f"Error (x,y,abs): {error}")

                # --- PID controller & coil driving ---
                if self.ctl_x and self.ctl_y:
                    pid_x_out = self.ctl_x.compute(pos[0])
                    pid_y_out = self.ctl_y.compute(pos[1])
                    self.x_coil.set_magnetic_field(pid_x_out)
                    self.y_coil.set_magnetic_field(pid_y_out)

            if self.show_pos_cursor:
                cv2.circle(display_frame, pos, radius=6, color=(255, 0, 0), thickness=2)
            self.position_label.setText(f"Position: {pos[0]}, {pos[1]}")
        else:
            self.position_label.setText("Position: None")

        if getattr(self, 'show_mask', False):
            self.display_frame(comp_mask, is_mask=True)
        else:
            self.display_frame(display_frame)

    # --- Render to QLabel ---
    def display_frame(self, frame, is_mask=False):
        if is_mask:
            h, w = frame.shape[:2]
            qimg = QImage(frame.data, w, h, frame.strides[0], QImage.Format.Format_Grayscale8)
        else:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            qimg = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format.Format_RGB888)

        pixmap = QPixmap.fromImage(qimg)

        label_w = self.video_label.width()
        label_h = self.video_label.height()

        scaled_pixmap = pixmap.scaled(label_w, label_h, Qt.AspectRatioMode.KeepAspectRatio)

        device_ratio = scaled_pixmap.devicePixelRatio()
        logical_pix_w = int(scaled_pixmap.width() / device_ratio)
        logical_pix_h = int(scaled_pixmap.height() / device_ratio)

        self._pixmap_size = (logical_pix_w, logical_pix_h)
        self._label_size = (label_w, label_h)
        self._frame_size = (w, h)

        self.video_label.setPixmap(scaled_pixmap)

    # --- Click handling ---
    def on_mouse_click(self, event):
        px = event.pos().x()
        py = event.pos().y()

        label_w, label_h = self._label_size
        pixmap_w, pixmap_h = self._pixmap_size

        if pixmap_w == 0 or pixmap_h == 0:
            return

        x_offset = (label_w - pixmap_w) // 2
        y_offset = (label_h - pixmap_h) // 2

        x_in = px - x_offset
        y_in = py - y_offset

        if x_in < 0 or y_in < 0 or x_in >= pixmap_w or y_in >= pixmap_h:
            return

        frame_w, frame_h = self._frame_size
        x_frame = int(x_in * frame_w / pixmap_w)
        y_frame = int(y_in * frame_h / pixmap_h)
        x_frame = max(0, min(frame_w - 1, x_frame))
        y_frame = max(0, min(frame_h - 1, y_frame))

        if self.roi_mask is None:
            if len(self.roi_points) < 4:
                self.roi_points.append((x_frame, y_frame))
                print(f"ROI point {len(self.roi_points)} = {(x_frame, y_frame)}")
                if len(self.roi_points) == 4:
                    self.roi_mask = np.zeros((frame_h, frame_w), dtype=np.uint8)
                    cv2.fillPoly(self.roi_mask, [np.array(self.roi_points, dtype=np.int32)], 255)
                    print("ROI set.")
        elif self.select_target_mode:
            if self.roi_mask[y_frame, x_frame] > 0:
                self.target = (x_frame, y_frame)
                print(f"New target set: {self.target}")
                self.ctl_x = ctlr.PID("x", kp=1.00, ki=0.10, kd=0.00,
                                      setpoint=self.target[0], output_limits=(-100, 100))
                self.ctl_y = ctlr.PID("y", kp=1.00, ki=0.10, kd=0.00,
                                      setpoint=self.target[1], output_limits=(-100, 100))
            else:
                print("Click ignored: outside ROI")

    def closeEvent(self, event):
        try:
            self.camera.release()
        except Exception:
            pass
        try:
            self.x_coil.cleanup()
            self.y_coil.cleanup()
        except Exception:
            pass
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = CameraWidget()
    win.show()
    sys.exit(app.exec())
