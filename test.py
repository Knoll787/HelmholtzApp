import sys
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QGridLayout, QHBoxLayout, QComboBox, QTabWidget, QMainWindow, QMenu
)

from hardware import coils



"""
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
"""	
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QGridLayout, 
                            QLabel, QPushButton, QHBoxLayout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.coil_data = self.initialize_coil_data()
        self.setup_ui()
        
    def initialize_coil_data(self):
        """Create data structure for all coil information"""
        return {
            'stats': {
                f'coil_{i}': {
                    'name': f'Coil {i}',
                    'pwm': {'value': 0, 'label': None, 'unit': '%'},
                    'current': {'value': 0, 'label': None, 'unit': 'A'}
                } for i in range(1, 7)  # Coils 1-6
            },
            'controls': {
                'buttons': ['Reset', 'Set']
            }
        }

    def setup_ui(self):
        """Initialize all UI components"""
        self.setWindowTitle("Coil Interface")
        self.setFixedSize(640, 640)

        # Main layout and central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create and add all components
        self.create_stats_section(main_layout)
        self.create_control_section(main_layout)
        self.create_state_section(main_layout)

    def create_stats_section(self, parent_layout):
        """Create the statistics display grid"""
        stats_widget = QWidget()
        stats_layout = QGridLayout(stats_widget)

        # Add title
        stats_layout.addWidget(QLabel("System Stats"), 0, 0, 1, 8)

        # Create coil stat displays using data structure
        for i, (coil_id, coil) in enumerate(self.coil_data['stats'].items()):
            row = 1 + (i // 2) * 2  # 1, 1, 3, 3, 5, 5
            col = 0 if i % 2 == 0 else 4  # Alternating columns

            # Add coil name
            stats_layout.addWidget(QLabel(coil['name']), row, col)

            # Create and add PWM display
            pwm_label = QLabel(str(coil['pwm']['value']))
            coil['pwm']['label'] = pwm_label
            stats_layout.addWidget(QLabel(f"PWM [{coil['pwm']['unit']}]:"), row + 1, col)
            stats_layout.addWidget(pwm_label, row + 1, col + 1)

            # Create and add current display
            current_label = QLabel(str(coil['current']['value']))
            coil['current']['label'] = current_label
            stats_layout.addWidget(QLabel(f"Current [{coil['current']['unit']}]:"), row + 1, col + 2)
            stats_layout.addWidget(current_label, row + 1, col + 3)

        parent_layout.addWidget(stats_widget)

    def create_control_section(self, parent_layout):
        """Create the control section"""
        control_widget = QWidget()
        control_layout = QGridLayout(control_widget)
        control_layout.addWidget(QLabel("Coil Control"))
        
        # Here you would add control elements using the same data-driven approach
        # Example: for each coil, add sliders/buttons for PWM and current control
        
        parent_layout.addWidget(control_widget)

    def create_state_section(self, parent_layout):
        """Create the state/action buttons section"""
        state_widget = QWidget()
        state_layout = QHBoxLayout(state_widget)

        # Create buttons from data structure
        for btn_text in self.coil_data['controls']['buttons']:
            button = QPushButton(btn_text)
            setattr(self, f'btn_{btn_text.lower()}', button)
            state_layout.addWidget(button)

        parent_layout.addWidget(state_widget)

    def update_coil_value(self, coil_num, pwm=None, current=None):
        """Update displayed coil values"""
        coil = self.coil_data['stats'][f'coil_{coil_num}']
        
        if pwm is not None:
            coil['pwm']['value'] = pwm
            coil['pwm']['label'].setText(str(pwm))
            
        if current is not None:
            coil['current']['value'] = current
            coil['current']['label'].setText(str(current))


def main():
	app = QApplication(sys.argv)

	app.setStyle('Fusion')
	window = MainWindow()
	window.show()

	sys.exit(app.exec())
	

if __name__ == '__main__':
	main()