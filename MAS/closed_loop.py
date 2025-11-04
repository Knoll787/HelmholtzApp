import sys
import cv2
import numpy as np
from PyQt6.QtCore import QTimer, Qt, QPoint
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

        self.setWindowTitle("Tracking GUI - Line Following")
        self.setFixedSize(700, 700)

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

        # --- Path drawing state (mouse inside ROI) ---
        self.draw_mode = False
        self.drawing = False           # True while mouse is pressed & moving
        self.overlay_points = []       # list of (x_frame, y_frame) waypoints (virtual path)
        self.current_target_idx = 0
        self.path_follow_mode = False
        self.advance_radius = 8       # pixels threshold to advance to next waypoint
        self._last_draw_point = None   # last point sampled while dragging

        # --- Video feed as main focus ---
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        # Bind mouse event handlers (we'll map positions using existing on_mouse_click helper)
        self.video_label.mousePressEvent = self._mouse_press_event
        self.video_label.mouseMoveEvent = self._mouse_move_event
        self.video_label.mouseReleaseEvent = self._mouse_release_event

        # --- Controls and info ---
        self.toggle_button = QPushButton("Show Mask")
        self.toggle_button.clicked.connect(self.toggle_view)

        self.toggle_target_button = QPushButton("Select Target")
        self.toggle_target_button.setCheckable(True)
        self.toggle_target_button.clicked.connect(self.toggle_target_mode)

        self.cursor_button = QPushButton("Hide Cursor")
        self.cursor_button.setCheckable(True)
        self.cursor_button.clicked.connect(self.toggle_cursor)

        self.start_stop_button = QPushButton("Start")
        self.start_stop_button.setCheckable(True)
        self.start_stop_button.clicked.connect(self.toggle_start_stop)

        self.draw_path_button = QPushButton("Draw Path")
        self.draw_path_button.setCheckable(True)
        self.draw_path_button.clicked.connect(self.toggle_draw_mode)
        self.draw_path_button.setEnabled(False)  # only enable after ROI defined

        self.clear_path_button = QPushButton("Clear Path")
        self.clear_path_button.clicked.connect(self.clear_path)
        self.clear_path_button.setEnabled(False)

        self.position_label = QLabel("Position: -,-")
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position_label.setFixedWidth(130)

        self.error_label = QLabel("Error: -,-")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setFixedWidth(150)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.toggle_button)
        bottom_layout.addWidget(self.toggle_target_button)
        bottom_layout.addWidget(self.cursor_button)
        bottom_layout.addWidget(self.start_stop_button)
        bottom_layout.addWidget(self.draw_path_button)
        bottom_layout.addWidget(self.clear_path_button)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.position_label)
        bottom_layout.addWidget(self.error_label)

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
        # create controllers, setpoint will be set per waypoint during following
        self.ctl_x = ctlr.PID("x", kp=1.0, ki=0.0, kd=0.0, setpoint=0, output_limits=(-60, 60))
        self.ctl_y = ctlr.PID("y", kp=5.0, ki=0.0, kd=0.0, setpoint=0, output_limits=(-60, 60))

        # Start/stop flag
        self.running = False

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

    def toggle_start_stop(self):
        # When Start pressed, begin path-following if overlay_points exist. Otherwise behave as before for single target.
        self.running = self.start_stop_button.isChecked()
        if self.running:
            # Start path-following if a path exists; else if a single target exists, resume single target behavior
            if self.overlay_points:
                self.path_follow_mode = True
                self.current_target_idx = 0
                wp = self.overlay_points[0]
                self.ctl_x.setpoint = wp[0]
                self.ctl_y.setpoint = wp[1]
                self.start_stop_button.setText("Stop")
                print("Path-following started.")
            else:
                # existing single-target start behavior
                self.path_follow_mode = False
                self.start_stop_button.setText("Stop")
                print("Coils activated. Tracking started.")
        else:
            # Stop all control
            self.start_stop_button.setText("Start")
            self.ctl_x = ctlr.PID("x", kp=self.ctl_x.kp, ki=self.ctl_x.ki, kd=self.ctl_x.kd,
                                 setpoint=0, output_limits=self.ctl_x.output_limits)
            self.ctl_y = ctlr.PID("y", kp=self.ctl_y.kp, ki=self.ctl_y.ki, kd=self.ctl_y.kd,
                                 setpoint=0, output_limits=self.ctl_y.output_limits)
            self.target = None
            self.position_label.setText("Position: -,-")
            self.error_label.setText("Error: -,-")
            self.x_coil.set_magnetic_field(0)
            self.y_coil.set_magnetic_field(0)
            self.path_follow_mode = False
            print("Coils deactivated. Target cleared.")

    def toggle_draw_mode(self):
        self.draw_mode = self.draw_path_button.isChecked()
        self.draw_path_button.setText("Drawing..." if self.draw_mode else "Draw Path")
        # Only allow drawing if ROI exists
        if self.draw_mode and self.roi_mask is None:
            # disable drawing when ROI not set
            self.draw_mode = False
            self.draw_path_button.setChecked(False)
            self.draw_path_button.setEnabled(False)
            print("Draw Path requires ROI to be set. Define ROI first (4 clicks).")

    def clear_path(self):
        self.overlay_points = []
        self.current_target_idx = 0
        self.clear_path_button.setEnabled(False)
        print("Path cleared.")

    # --- Mouse-based drawing inside ROI ---
    def _mouse_press_event(self, event):
        # map click to frame coordinates
        coords = self._map_label_to_frame(event.pos())
        if coords is None:
            return
        x_frame, y_frame = coords

        # If ROI not set, fall back to original ROI-point collection
        if self.roi_mask is None:
            if len(self.roi_points) < 4:
                self.roi_points.append((x_frame, y_frame))
                print(f"ROI point {len(self.roi_points)} = {(x_frame, y_frame)}")
                if len(self.roi_points) == 4:
                    frame_h = self._frame_size[1]
                    frame_w = self._frame_size[0]
                    self.roi_mask = np.zeros((frame_h, frame_w), dtype=np.uint8)
                    cv2.fillPoly(self.roi_mask, [np.array(self.roi_points, dtype=np.int32)], 255)
                    print("ROI set.")
                    # enable draw path button now ROI exists
                    self.draw_path_button.setEnabled(True)
                    self.clear_path_button.setEnabled(True)
            return

        # If draw mode enabled, start drawing only if click inside ROI
        if self.draw_mode:
            if self.roi_mask[y_frame, x_frame] > 0:
                self.drawing = True
                self._append_draw_point((x_frame, y_frame))
                self._last_draw_point = (x_frame, y_frame)
            else:
                print("Click ignored: outside ROI for drawing.")
            return

        # If select_target_mode, set target as before
        if self.select_target_mode:
            if self.roi_mask[y_frame, x_frame] > 0:
                self.target = (x_frame, y_frame)
                print(f"New target set: {self.target}")
                self.ctl_x.setpoint = self.target[0]
                self.ctl_y.setpoint = self.target[1]
            else:
                print("Click ignored: outside ROI")
            return

        # Otherwise, treat click as adding a single waypoint (if user prefers clicking)
        if self.roi_mask[y_frame, x_frame] > 0:
            self.overlay_points.append((x_frame, y_frame))
            self.clear_path_button.setEnabled(True)
            print("Added waypoint (mouse):", (x_frame, y_frame))

    def _mouse_move_event(self, event):
        if not self.drawing:
            return
        coords = self._map_label_to_frame(event.pos())
        if coords is None:
            return
        x_frame, y_frame = coords
        # Only add if inside ROI and moved enough distance to avoid flooding
        if self.roi_mask is None:
            return
        if self.roi_mask[y_frame, x_frame] == 0:
            return
        last = self._last_draw_point
        if last is None or (abs(last[0] - x_frame) >= 3 or abs(last[1] - y_frame) >= 3):
            self._append_draw_point((x_frame, y_frame))
            self._last_draw_point = (x_frame, y_frame)

    def _mouse_release_event(self, event):
        if self.drawing:
            self.drawing = False
            self._last_draw_point = None

    def _append_draw_point(self, pt):
        # Avoid adding identical sequential points
        if not self.overlay_points or self.overlay_points[-1] != pt:
            self.overlay_points.append(pt)
            self.clear_path_button.setEnabled(True)

    def _map_label_to_frame(self, qpoint: QPoint):
        """Map a QPoint in label coordinates to frame pixel coordinates.
           Returns (x_frame, y_frame) or None if outside the displayed pixmap."""
        px = int(qpoint.x())
        py = int(qpoint.y())

        label_w, label_h = self._label_size
        pixmap_w, pixmap_h = self._pixmap_size

        if pixmap_w == 0 or pixmap_h == 0:
            return None

        x_offset = (label_w - pixmap_w) // 2
        y_offset = (label_h - pixmap_h) // 2

        x_in = px - x_offset
        y_in = py - y_offset

        if x_in < 0 or y_in < 0 or x_in >= pixmap_w or y_in >= pixmap_h:
            return None

        frame_w, frame_h = self._frame_size
        x_frame = int(x_in * frame_w / pixmap_w)
        y_frame = int(y_in * frame_h / pixmap_h)
        x_frame = max(0, min(frame_w - 1, x_frame))
        y_frame = max(0, min(frame_h - 1, y_frame))
        return x_frame, y_frame

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

        if pos is not None:
            if self.show_pos_cursor:
                cv2.circle(display_frame, pos, radius=6, color=(255, 0, 0), thickness=2)

            # --- Position display ---
            self.position_label.setText(f"Position: {pos[0]:.1f}, {pos[1]:.1f}")

            # --- Line-following or single-target behavior ---
            if self.path_follow_mode and self.overlay_points and self.running:
                # ensure current index is valid
                if self.current_target_idx >= len(self.overlay_points):
                    self.current_target_idx = len(self.overlay_points) - 1

                waypoint = self.overlay_points[self.current_target_idx]
                cv2.circle(display_frame, waypoint, radius=5, color=(0, 0, 255), thickness=2)

                # compute error (use ip.calculate_error if available)
                try:
                    err_x, err_y, err_abs = ip.calculate_error(pos, waypoint)
                except Exception:
                    err_x = waypoint[0] - pos[0]
                    err_y = waypoint[1] - pos[1]
                    err_abs = (err_x ** 2 + err_y ** 2) ** 0.5

                self.error_label.setText(f"Error: {err_x:.1f}, {err_y:.1f} (|{err_abs:.1f}|)")

                # update PID setpoints to current waypoint and compute outputs
                try:
                    self.ctl_x.setpoint = waypoint[0]
                    self.ctl_y.setpoint = waypoint[1]
                    pid_x_out = self.ctl_x.compute(pos[0])
                    pid_y_out = self.ctl_y.compute(pos[1])
                except TypeError:
                    # some PID implementations accept setpoint as compute param
                    pid_x_out = self.ctl_x.compute(pos[0], setpoint=waypoint[0])
                    pid_y_out = self.ctl_y.compute(pos[1], setpoint=waypoint[1])

                # apply outputs to coils
                self.x_coil.set_magnetic_field(pid_x_out)
                self.y_coil.set_magnetic_field(pid_y_out)

                # advance when close enough
                if err_abs < self.advance_radius:
                    if self.current_target_idx < len(self.overlay_points) - 1:
                        self.current_target_idx += 1
                        print("Advancing to waypoint", self.current_target_idx)
                    else:
                        # reached final waypoint: stop following
                        print("Reached final waypoint. Stopping.")
                        self.start_stop_button.setChecked(False)
                        self.toggle_start_stop()
            elif self.target is not None and self.running and not self.path_follow_mode:
                # original single-target PID behavior (unchanged)
                cv2.circle(display_frame, self.target, radius=6, color=(0, 0, 255), thickness=2)
                error = ip.calculate_error(pos, self.target)
                if error:
                    err_x, err_y, err_abs = error
                    self.error_label.setText(f"Error: {err_x:.1f}, {err_y:.1f} (|{err_abs:.1f}|)")
                    if self.ctl_x and self.ctl_y:
                        pid_x_out = self.ctl_x.compute(pos[0])
                        pid_y_out = self.ctl_y.compute(pos[1])
                        self.x_coil.set_magnetic_field(pid_x_out)
                        self.y_coil.set_magnetic_field(pid_y_out)
                else:
                    self.error_label.setText("Error: -,-")
            else:
                self.error_label.setText("Error: -,-")
        else:
            self.position_label.setText("Position: None")
            self.error_label.setText("Error: -,-")

        # Draw the overlay path (only inside ROI points)
        if len(self.overlay_points) >= 2:
            for i in range(1, len(self.overlay_points)):
                cv2.line(display_frame, self.overlay_points[i - 1], self.overlay_points[i], (0, 0, 255), 2)
        elif len(self.overlay_points) == 1:
            cv2.circle(display_frame, self.overlay_points[0], 3, (0, 0, 255), -1)

        # Draw ROI border again to keep it visible
        if len(self.roi_points) >= 2:
            cv2.polylines(display_frame, [np.array(self.roi_points, dtype=np.int32)],
                          isClosed=True, color=(0, 255, 255), thickness=1)

        if getattr(self, 'show_mask', False):
            # If mask display desired, try to show comp_mask
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

    # --- close event cleanup ---
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
