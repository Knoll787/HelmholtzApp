import sys
import subprocess
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt

class ScriptLauncher(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Python Script Launcher")
        self.process = None  # Track running script

        layout = QVBoxLayout()

        # Title
        title = QLabel("Magnetic Actuation System")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # Brief description
        description = QLabel("Below are buttons to launch various Python scripts for controlling the Magnetic Actuation System." \
                             "Click a button to run the corresponding script. " \
                             "Note that only one script can run at a time.\n")
        description.setAlignment(Qt.AlignmentFlag.AlignLeft)
        description.setWordWrap(True)
        layout.addWidget(description)

        # Button + description setup
        self.scripts = [
            ("Coil Control", "Manually set the current and direction of each coil", "tests/coil_control.py"),
            ("Open Loop", "Manipulate objects within the workspace using a controller", "tests/open_loop.py"),
            ("Closed-loop", "Full access to the closed loop control scheme", "script4.py"),
            ("Debug", "Closed Loop control with pre-set parameters e.g. ROI ", "script3.py"),
        ]

        for name, desc, script in self.scripts:
            h_layout = QHBoxLayout()

            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, s=script: self.run_script(s))

            label = QLabel(desc)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            h_layout.addWidget(btn)
            h_layout.addWidget(label, stretch=1)

            layout.addLayout(h_layout)

        self.setLayout(layout)

    def run_script(self, script_name):
        # Prevent multiple scripts running at once
        if self.process and self.process.poll() is None:
            QMessageBox.warning(self, "Script Running", "Another script is already running. Please stop it first.")
            return

        try:
            self.process = subprocess.Popen([sys.executable, script_name])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run {script_name}: {e}")

    def closeEvent(self, event):
        # Kill process on exit
        if self.process and self.process.poll() is None:
            self.process.terminate()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScriptLauncher()
    window.show()
    sys.exit(app.exec())