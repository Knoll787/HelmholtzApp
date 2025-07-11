import sys
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QGridLayout, QHBoxLayout, QComboBox, QTabWidget, QMainWindow
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
		self.label1 = QLabel("System Stats")
		stats_layout = QGridLayout(stats_widget)
		stats_layout.addWidget(self.label1)
		
		control_widget = QWidget(central_widget)
		self.label2 = QLabel("Coil Control")
		control_layout = QGridLayout(control_widget)
		control_layout.addWidget(self.label2)

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