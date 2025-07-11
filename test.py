from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QGridLayout, 
                            QLabel, QPushButton, QHBoxLayout, QComboBox, 
                            QSlider, QGroupBox, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor

class DraculaTheme:
    """Dracula color palette constants"""
    BACKGROUND = QColor(40, 42, 54)
    CURRENT_LINE = QColor(68, 71, 90)
    FOREGROUND = QColor(248, 248, 242)
    COMMENT = QColor(98, 114, 164)
    CYAN = QColor(139, 233, 253)
    GREEN = QColor(80, 250, 123)
    ORANGE = QColor(255, 184, 108)
    PINK = QColor(255, 121, 198)
    PURPLE = QColor(189, 147, 249)
    RED = QColor(255, 85, 85)
    YELLOW = QColor(241, 250, 140)

def apply_dracula_theme(app):
    """Apply Dracula theme to the application"""
    palette = QPalette()
    
    # Base colors
    palette.setColor(QPalette.ColorRole.Window, DraculaTheme.BACKGROUND)
    palette.setColor(QPalette.ColorRole.WindowText, DraculaTheme.FOREGROUND)
    palette.setColor(QPalette.ColorRole.Base, DraculaTheme.CURRENT_LINE)
    palette.setColor(QPalette.ColorRole.AlternateBase, DraculaTheme.BACKGROUND)
    palette.setColor(QPalette.ColorRole.ToolTipBase, DraculaTheme.BACKGROUND)
    palette.setColor(QPalette.ColorRole.ToolTipText, DraculaTheme.FOREGROUND)
    palette.setColor(QPalette.ColorRole.Text, DraculaTheme.FOREGROUND)
    palette.setColor(QPalette.ColorRole.Button, DraculaTheme.BACKGROUND)
    palette.setColor(QPalette.ColorRole.ButtonText, DraculaTheme.FOREGROUND)
    palette.setColor(QPalette.ColorRole.BrightText, DraculaTheme.RED)
    palette.setColor(QPalette.ColorRole.Highlight, DraculaTheme.PURPLE)
    palette.setColor(QPalette.ColorRole.HighlightedText, DraculaTheme.FOREGROUND)
    
    # Disabled colors
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, DraculaTheme.COMMENT)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, DraculaTheme.COMMENT)
    
    app.setPalette(palette)
    
    # Additional style tweaks
    app.setStyleSheet(f"""
        QWidget {{
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
        }}
        
        QGroupBox {{
            border: 1px solid {DraculaTheme.COMMENT.name()};
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 15px;
            color: {DraculaTheme.PINK.name()};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
        }}
        
        QSlider::groove:horizontal {{
            background: {DraculaTheme.COMMENT.name()};
            height: 6px;
            border-radius: 3px;
        }}
        
        QSlider::handle:horizontal {{
            background: {DraculaTheme.PURPLE.name()};
            border: 1px solid {DraculaTheme.PINK.name()};
            width: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }}
        
        QSlider::sub-page:horizontal {{
            background: {DraculaTheme.PURPLE.name()};
            border-radius: 3px;
        }}
        
        QComboBox {{
            background: {DraculaTheme.CURRENT_LINE.name()};
            border: 1px solid {DraculaTheme.COMMENT.name()};
            border-radius: 4px;
            padding: 3px;
            min-width: 100px;
        }}
        
        QComboBox QAbstractItemView {{
            background: {DraculaTheme.CURRENT_LINE.name()};
            selection-background-color: {DraculaTheme.PURPLE.name()};
        }}
        
        QPushButton {{
            background: {DraculaTheme.CURRENT_LINE.name()};
            border: 1px solid {DraculaTheme.COMMENT.name()};
            border-radius: 4px;
            padding: 5px 10px;
            min-width: 80px;
        }}
        
        QPushButton:hover {{
            background: {DraculaTheme.PURPLE.name()};
            border-color: {DraculaTheme.PINK.name()};
        }}
        
        QLabel[accessibleName="title"] {{
            font-size: 14px;
            font-weight: bold;
            color: {DraculaTheme.CYAN.name()};
        }}
    """)

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
                'buttons': ['Reset', 'Set'],
                'axes': {
                    'X': {'type': 'Helmholtz', 'value': 0, 'slider': None, 'combo': None},
                    'Y': {'type': 'Helmholtz', 'value': 0, 'slider': None, 'combo': None},
                    'Z': {'type': 'Helmholtz', 'value': 0, 'slider': None, 'combo': None}
                }
            }
        }

    def setup_ui(self):
        """Initialize all UI components"""
        self.setWindowTitle("Coil Interface")
        self.setFixedSize(800, 800)

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
        title = QLabel("System Stats")
        title.setAccessibleName("title")
        stats_layout.addWidget(title, 0, 0, 1, 8)

        # Create coil stat displays using data structure
        for i, (coil_id, coil) in enumerate(self.coil_data['stats'].items()):
            row = 1 + (i // 2) * 2  # 1, 1, 3, 3, 5, 5
            col = 0 if i % 2 == 0 else 4  # Alternating columns

            # Add coil name
            name_label = QLabel(coil['name'])
            name_label.setStyleSheet(f"color: {DraculaTheme.GREEN.name()};")
            stats_layout.addWidget(name_label, row, col)

            # Create and add PWM display
            pwm_label = QLabel(str(coil['pwm']['value']))
            pwm_label.setStyleSheet(f"color: {DraculaTheme.YELLOW.name()};")
            coil['pwm']['label'] = pwm_label
            stats_layout.addWidget(QLabel(f"PWM [{coil['pwm']['unit']}]:"), row + 1, col)
            stats_layout.addWidget(pwm_label, row + 1, col + 1)

            # Create and add current display
            current_label = QLabel(str(coil['current']['value']))
            current_label.setStyleSheet(f"color: {DraculaTheme.ORANGE.name()};")
            coil['current']['label'] = current_label
            stats_layout.addWidget(QLabel(f"Current [{coil['current']['unit']}]:"), row + 1, col + 2)
            stats_layout.addWidget(current_label, row + 1, col + 3)

        parent_layout.addWidget(stats_widget)

    def create_control_section(self, parent_layout):
        """Create the control section with axis controls"""
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # Add title
        title = QLabel("Coil Control")
        title.setAccessibleName("title")
        control_layout.addWidget(title)
        
        # Create axis control group
        axis_group = QGroupBox("Axis Configuration")
        axis_layout = QGridLayout()
        
        # Add row headers
        headers = ["Axis", "Coil Type", "Value"]
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setStyleSheet(f"color: {DraculaTheme.CYAN.name()}; font-weight: bold;")
            axis_layout.addWidget(label, 0, col)
        
        # Create controls for each axis
        for row, (axis, config) in enumerate(self.coil_data['controls']['axes'].items(), start=1):
            # Axis label
            axis_label = QLabel(f"{axis}-Axis")
            axis_label.setStyleSheet(f"color: {DraculaTheme.GREEN.name()};")
            axis_layout.addWidget(axis_label, row, 0)
            
            # Coil type dropdown
            coil_type_combo = QComboBox()
            coil_type_combo.addItems(["Helmholtz", "Maxwell"])
            coil_type_combo.setCurrentText(config['type'])
            coil_type_combo.currentTextChanged.connect(
                lambda text, a=axis: self.on_coil_type_changed(a, text))
            axis_layout.addWidget(coil_type_combo, row, 1)
            config['combo'] = coil_type_combo
            
            # Value slider
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(-100, 100)
            slider.setValue(0)
            slider.setTickPosition(QSlider.TickPosition.TicksBelow)
            slider.setTickInterval(10)
            slider.valueChanged.connect(
                lambda value, a=axis: self.on_slider_changed(a, value))
            axis_layout.addWidget(slider, row, 2)
            config['slider'] = slider
            
            # Value display label
            value_label = QLabel("0")
            value_label.setStyleSheet(f"color: {DraculaTheme.YELLOW.name()}; min-width: 30px;")
            axis_layout.addWidget(value_label, row, 3)
            config['label'] = value_label
        
        axis_group.setLayout(axis_layout)
        control_layout.addWidget(axis_group)
        
        parent_layout.addWidget(control_widget)

    def create_state_section(self, parent_layout):
        """Create the state/action buttons section"""
        state_widget = QWidget()
        state_layout = QHBoxLayout(state_widget)

        # Create buttons from data structure
        for btn_text in self.coil_data['controls']['buttons']:
            button = QPushButton(btn_text)
            button.setStyleSheet(f"""
                QPushButton {{
                    background: {DraculaTheme.PURPLE.name()};
                    color: {DraculaTheme.FOREGROUND.name()};
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {DraculaTheme.PINK.name()};
                }}
            """)
            setattr(self, f'btn_{btn_text.lower()}', button)
            if btn_text == "Reset":
                button.clicked.connect(self.reset_sliders)
            state_layout.addWidget(button)

        parent_layout.addWidget(state_widget)

    def on_coil_type_changed(self, axis, coil_type):
        """Handle coil type selection changes"""
        self.coil_data['controls']['axes'][axis]['type'] = coil_type
        print(f"{axis}-Axis changed to {coil_type} coil")

    def on_slider_changed(self, axis, value):
        """Handle slider value changes"""
        self.coil_data['controls']['axes'][axis]['value'] = value
        self.coil_data['controls']['axes'][axis]['label'].setText(str(value))
        print(f"{axis}-Axis value: {value}")

    def reset_sliders(self):
        """Reset all sliders to 0"""
        for axis, config in self.coil_data['controls']['axes'].items():
            config['slider'].setValue(0)
            config['label'].setText("0")
            config['value'] = 0
        print("All sliders reset to 0")

    def update_coil_value(self, coil_num, pwm=None, current=None):
        """Update displayed coil values"""
        coil = self.coil_data['stats'][f'coil_{coil_num}']
        
        if pwm is not None:
            coil['pwm']['value'] = pwm
            coil['pwm']['label'].setText(str(pwm))
            
        if current is not None:
            coil['current']['value'] = current
            coil['current']['label'].setText(str(current))

if __name__ == "__main__":
    app = QApplication([])
    apply_dracula_theme(app)
    window = MainWindow()
    window.show()
    app.exec()