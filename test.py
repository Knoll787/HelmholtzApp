import sys
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QGridLayout, QHBoxLayout, QComboBox, QTabWidget, QMainWindow, QMenu
)

from hardware import coils



class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setup_ui()
		
	def setup_ui(self):
		self.setWindowTitle("Coil Interface")
		self.setFixedSize(640, 640)

		central_widget = QWidget()
		self.setCentralWidget(central_widget)
		layout = QVBoxLayout(central_widget)
		

		stats_widget = QWidget(central_widget)
		label_coil1_pwm = QLabel("0")
		label_coil1_current = QLabel("0")
		label_coil2_pwm = QLabel("0")
		label_coil2_current = QLabel("0")
		label_coil3_pwm = QLabel("0")
		label_coil3_current = QLabel("0")
		label_coil4_pwm = QLabel("0")
		label_coil4_current = QLabel("0")
		label_coil5_pwm = QLabel("0")
		label_coil5_current = QLabel("0")
		label_coil6_pwm = QLabel("0")
		label_coil6_current = QLabel("0")

		stats_layout = QGridLayout(stats_widget)
		stats_layout.addWidget(QLabel("System Stats"), 0, 0)

		stats_layout.addWidget(QLabel("Coil 1"),       1, 0)
		stats_layout.addWidget(QLabel("PWM [%]:"),     2, 0)
		stats_layout.addWidget(label_coil1_pwm,        2, 1)
		stats_layout.addWidget(QLabel("Current [A]:"), 2, 2)
		stats_layout.addWidget(label_coil1_current,    2, 3)

		stats_layout.addWidget(QLabel("Coil 2"),       1, 4)
		stats_layout.addWidget(QLabel("PWM [%]:"),     2, 4)
		stats_layout.addWidget(label_coil2_pwm,        2, 5)
		stats_layout.addWidget(QLabel("Current [A]:"), 2, 6)
		stats_layout.addWidget(label_coil2_current,    2, 7)
		
		stats_layout.addWidget(QLabel("Coil 3"),       3, 0)
		stats_layout.addWidget(QLabel("PWM [%]:"),     4, 0)
		stats_layout.addWidget(label_coil3_pwm,        4, 1)
		stats_layout.addWidget(QLabel("Current [A]:"), 4, 2)
		stats_layout.addWidget(label_coil3_current,    4, 3)

		stats_layout.addWidget(QLabel("Coil 4"),       3, 4)
		stats_layout.addWidget(QLabel("PWM [%]:"),     4, 4)
		stats_layout.addWidget(label_coil4_pwm,        4, 5)
		stats_layout.addWidget(QLabel("Current [A]:"), 4, 6)
		stats_layout.addWidget(label_coil4_current,    4, 7)
		
		stats_layout.addWidget(QLabel("Coil 5"),       5, 0)
		stats_layout.addWidget(QLabel("PWM [%]:"),     6, 0)
		stats_layout.addWidget(label_coil5_pwm,        6, 1)
		stats_layout.addWidget(QLabel("Current [A]:"), 6, 2)
		stats_layout.addWidget(label_coil5_current,    6, 3)

		stats_layout.addWidget(QLabel("Coil 6"),       5, 4)
		stats_layout.addWidget(QLabel("PWM [%]:"),     6, 4)
		stats_layout.addWidget(label_coil6_pwm,        6, 5)
		stats_layout.addWidget(QLabel("Current [A]:"), 6, 6)
		stats_layout.addWidget(label_coil6_current,    6, 7)
		
		




		control_widget = QWidget(central_widget)
		self.label2 = QLabel("Coil Control")
		control_layout = QGridLayout(control_widget)
		control_layout.addWidget(QLabel("Coil Control"))

		






		state_widget = QWidget(central_widget)
		self.btn_reset = QPushButton("Reset")	
		self.btn_set = QPushButton("Set")	
		state_layout = QHBoxLayout(state_widget)
		state_layout.addWidget(self.btn_reset)
		state_layout.addWidget(self.btn_set)

		
		
		layout.addWidget(stats_widget)
		layout.addWidget(control_widget)
		layout.addWidget(state_widget)
		


def main():
	app = QApplication(sys.argv)

	app.setStyle('Fusion')
	window = MainWindow()
	window.show()

	sys.exit(app.exec())
	

if __name__ == '__main__':
	main()