from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel
from PyQt6.QtCore import Qt
from theme import DraculaTheme

class CoilStatsWidget(QWidget):
    def __init__(self, coil_data):
        super().__init__()
        self.coil_data = coil_data
        self.init_ui()
        self.setStyleSheet(f"""
            QLabel {{
                padding: 2px;
            }}
        """)

    def init_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(10)
        
        # Add title
        title = QLabel("System Stats")
        title.setAccessibleName("title")
        title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {DraculaTheme.CYAN.name()};
            padding-bottom: 10px;
        """)
        layout.addWidget(title, 0, 0, 1, 8)

        # Create coil stat displays
        for i, (coil_id, coil) in enumerate(self.coil_data.stats.items()):
            row = 1 + (i // 2) * 2
            col = 0 if i % 2 == 0 else 4

            # Coil name
            name_label = QLabel(coil['name'])
            name_label.setStyleSheet(f"color: {DraculaTheme.GREEN.name()};")
            layout.addWidget(name_label, row, col)

            # PWM display
            pwm_label = QLabel(str(coil['pwm'].value))
            pwm_label.setStyleSheet(f"""
                color: {DraculaTheme.YELLOW.name()};
                min-width: 40px;
            """)
            coil['pwm'].label = pwm_label
            layout.addWidget(QLabel(f"PWM [{coil['pwm'].unit}]:"), row + 1, col)
            layout.addWidget(pwm_label, row + 1, col + 1)

            # Current display
            current_label = QLabel(str(coil['current'].value))
            current_label.setStyleSheet(f"""
                color: {DraculaTheme.ORANGE.name()};
                min-width: 40px;
            """)
            coil['current'].label = current_label
            layout.addWidget(QLabel(f"Current [{coil['current'].unit}]:"), row + 1, col + 2)
            layout.addWidget(current_label, row + 1, col + 3)