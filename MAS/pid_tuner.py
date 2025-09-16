import sys
import time
import threading
from collections import deque

import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets

# Camera imports (picamera2)
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except Exception:
    PICAMERA2_AVAILABLE = False

# Matplotlib embedding
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class CameraThread(QtCore.QThread):
    frame_ready = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, resolution=(320, 240), framerate=24, parent=None):
        super().__init__(parent)
        self.resolution = resolution
        self.framerate = framerate
        self._running = False
        self._camera = None

    def run(self):
        if not PICAMERA2_AVAILABLE:
            # emit a placeholder image every frame
            self._running = True
            while self._running:
                img = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
                t = time.time()
                cx = int((np.sin(t) * 0.5 + 0.5) * (self.resolution[0]-1))
                cy = int((np.cos(t) * 0.5 + 0.5) * (self.resolution[1]-1))
                img[cy-2:cy+2, cx-2:cx+2] = [0, 255, 0]
                self.frame_ready.emit(img)
                time.sleep(1.0/self.framerate)
            return

        # Real picamera2 capture
        self._camera = Picamera2()
        config = self._camera.create_preview_configuration(main={"size": self.resolution})
        self._camera.configure(config)
        self._camera.start()
        self._running = True

        while self._running:
            frame = self._camera.capture_array()
            if frame is not None:
                self.frame_ready.emit(frame)
            time.sleep(1.0/self.framerate)

        try:
            self._camera.stop()
        except Exception:
            pass

    def stop(self):
        self._running = False
        self.wait(500)


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        fig.tight_layout()


def compute_step_metrics(t, signal, final_value=None, tolerance=0.02):
    if len(t) == 0 or len(signal) == 0:
        return {}
    t = np.array(t)
    sig = np.array(signal)
    if final_value is None:
        last_n = max(1, int(0.1 * len(sig)))
        final_value = np.mean(sig[-last_n:])
    sse = final_value - sig[-1]
    v10 = 0.1 * final_value
    v90 = 0.9 * final_value
    try:
        idx10 = np.where(sig >= v10)[0][0]
        idx90 = np.where(sig >= v90)[0][0]
        rise_time = t[idx90] - t[idx10]
    except Exception:
        rise_time = np.nan
    peak = np.max(sig)
    if final_value != 0:
        overshoot = 100.0 * (peak - final_value) / abs(final_value)
    else:
        overshoot = np.nan
    tol = tolerance * abs(final_value)
    settling_time = np.nan
    within = np.abs(sig - final_value) <= tol
    try:
        if np.all(within):
            settling_time = t[0]
        else:
            for i in range(len(within)):
                if np.all(within[i:]):
                    settling_time = t[i]
                    break
    except Exception:
        settling_time = np.nan
    return {
        'final_value': float(final_value),
        'steady_state_error': float(sse),
        'rise_time': float(rise_time) if not np.isnan(rise_time) else None,
        'overshoot_percent': float(overshoot) if not np.isnan(overshoot) else None,
        'settling_time': float(settling_time) if not np.isnan(settling_time) else None,
    }


class PIDTunerApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PID Tuner — Magnetic Actuation')
        self.setGeometry(100, 100, 1000, 700)

        self.video_label = QtWidgets.QLabel()
        self.video_label.setFixedSize(480, 360)
        self.video_label.setStyleSheet('background-color: black;')

        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.canvas.setFixedSize(480, 360)

        top_layout = QtWidgets.QHBoxLayout()
        top_layout.addWidget(self.video_label)
        top_layout.addWidget(self.canvas)

        left_form = QtWidgets.QFormLayout()
        self.run_time_input = QtWidgets.QLineEdit('10.0')
        self.x_target_input = QtWidgets.QLineEdit('0.0')
        self.y_target_input = QtWidgets.QLineEdit('0.0')
        left_form.addRow('Total run time (s):', self.run_time_input)
        left_form.addRow('X target (units):', self.x_target_input)
        left_form.addRow('Y target (units):', self.y_target_input)

        left_widget = QtWidgets.QWidget()
        left_widget.setLayout(left_form)

        right_form = QtWidgets.QFormLayout()
        self.kp_input = QtWidgets.QLineEdit('1.0')
        self.ki_input = QtWidgets.QLineEdit('0.0')
        self.kd_input = QtWidgets.QLineEdit('0.0')
        right_form.addRow('Kp:', self.kp_input)
        right_form.addRow('Ki:', self.ki_input)
        right_form.addRow('Kd:', self.kd_input)

        right_widget = QtWidgets.QWidget()
        right_widget.setLayout(right_form)

        middle_layout = QtWidgets.QHBoxLayout()
        middle_layout.addWidget(left_widget)
        middle_layout.addStretch(1)
        middle_layout.addWidget(right_widget)

        self.run_button = QtWidgets.QPushButton('Run Test')
        self.run_button.clicked.connect(self.on_run_test)

        main_vbox = QtWidgets.QVBoxLayout()
        main_vbox.addLayout(top_layout)
        main_vbox.addLayout(middle_layout)
        main_vbox.addWidget(self.run_button)
        self.setLayout(main_vbox)

        self.cam_thread = CameraThread(resolution=(480, 360), framerate=24)
        self.cam_thread.frame_ready.connect(self.update_video_frame)
        self.cam_thread.start()

        self.run_lock = threading.Lock()
        self.t_data = []
        self.x_error = []
        self.y_error = []
        self._running_test = False

    def closeEvent(self, event):
        try:
            self.cam_thread.stop()
        except Exception:
            pass
        event.accept()

    @QtCore.pyqtSlot(np.ndarray)
    def update_video_frame(self, img):
        if img is None:
            return
        if img.shape[2] == 3:
            qimg = QtGui.QImage(img.data, img.shape[1], img.shape[0], img.strides[0], QtGui.QImage.Format_RGB888)
        else:
            qimg = QtGui.QImage(img.data, img.shape[1], img.shape[0], img.strides[0], QtGui.QImage.Format_Indexed8)
        pix = QtGui.QPixmap.fromImage(qimg).scaled(self.video_label.size(), QtCore.Qt.KeepAspectRatio)
        self.video_label.setPixmap(pix)

    def on_run_test(self):
        if self._running_test:
            QtWidgets.QMessageBox.warning(self, 'Test running', 'A test is already running.')
            return
        try:
            total_time = float(self.run_time_input.text())
            x_target = float(self.x_target_input.text())
            y_target = float(self.y_target_input.text())
            kp = float(self.kp_input.text())
            ki = float(self.ki_input.text())
            kd = float(self.kd_input.text())
        except ValueError:
            QtWidgets.QMessageBox.critical(self, 'Input error', 'Check that all inputs are numeric.')
            return
        with self.run_lock:
            self.t_data = []
            self.x_error = []
            self.y_error = []
        self._running_test = True
        self.run_button.setEnabled(False)
        t = threading.Thread(target=self.run_test, args=(total_time, x_target, y_target, kp, ki, kd), daemon=True)
        t.start()

    def run_test(self, total_time, x_target, y_target, kp, ki, kd):
        dt = 0.02
        steps = int(max(1, total_time / dt))
        ix = 0.0
        iy = 0.0
        prev_ex = 0.0
        prev_ey = 0.0
        x = 0.0
        y = 0.0
        vx = 0.0
        vy = 0.0
        start_time = time.time()
        for i in range(steps):
            now = time.time() - start_time
            measured_x = x
            measured_y = y
            ex = x_target - measured_x
            ey = y_target - measured_y
            ix += ex * dt
            iy += ey * dt
            dx = (ex - prev_ex) / dt
            dy = (ey - prev_ey) / dt
            ux = kp * ex + ki * ix + kd * dx
            uy = kp * ey + ki * iy + kd * dy
            prev_ex = ex
            prev_ey = ey
            ax = ux - 0.4 * vx - 0.1 * x
            ay = uy - 0.4 * vy - 0.1 * y
            vx += ax * dt
            vy += ay * dt
            x += vx * dt
            y += vy * dt
            with self.run_lock:
                self.t_data.append(now)
                self.x_error.append(ex)
                self.y_error.append(ey)
            time.sleep(dt)
        self._running_test = False
        QtCore.QMetaObject.invokeMethod(self, 'on_test_finished', QtCore.Qt.QueuedConnection)

    @QtCore.pyqtSlot()
    def on_test_finished(self):
        self.run_button.setEnabled(True)
        with self.run_lock:
            t = list(self.t_data)
            x_err = list(self.x_error)
            y_err = list(self.y_error)
        self.canvas.ax.clear()
        if len(t) == 0:
            self.canvas.ax.text(0.5, 0.5, 'No data collected', ha='center')
            self.canvas.draw()
            return
        self.canvas.ax.plot(t, x_err, label='x error')
        self.canvas.ax.plot(t, y_err, label='y error')
        self.canvas.ax.set_xlabel('Time (s)')
        self.canvas.ax.set_ylabel('Error (units)')
        self.canvas.ax.legend()
        mx = compute_step_metrics(t, [-v for v in x_err], final_value=0.0)
        my = compute_step_metrics(t, [-v for v in y_err], final_value=0.0)
        txt_lines = [f'X: rise={mx.get("rise_time"):0.3f}s overshoot={mx.get("overshoot_percent"):0.2f}% settling={mx.get("settling_time"):0.3f}s sse={mx.get("steady_state_error"):0.3f}']
        txt_lines.append(f'Y: rise={my.get("rise_time"):0.3f}s overshoot={my.get("overshoot_percent"):0.2f}% settling={my.get("settling_time"):0.3f}s sse={my.get("steady_state_error"):0.3f}')
        props = dict(boxstyle='round', facecolor='white', alpha=0.7)
        self.canvas.ax.text(0.02, 0.98, '\n'.join(txt_lines), transform=self.canvas.ax.transAxes, fontsize=9,
                            verticalalignment='top', bbox=props)
        self.canvas.draw()


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = PIDTunerApp()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
