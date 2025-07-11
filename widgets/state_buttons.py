from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, 
                            QSpacerItem, QSizePolicy)
from theme import DraculaTheme

class StateButtonsWidget(QWidget):
    def __init__(self, coil_data):
        super().__init__()
        self.coil_data = coil_data
        self.init_ui()

    def init_ui(self):
        # Create main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 10, 0, 0)
        
        # Create a container widget for centered buttons
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(15)
        
        # Add stretchable space before buttons
        main_layout.addStretch()
        
        # Add buttons to the centered layout
        for btn_text in self.coil_data.controls['buttons']:
            button = QPushButton(btn_text)
            button.setStyleSheet(f"""
                QPushButton {{
                    background: {DraculaTheme.PURPLE.name()};
                    color: {DraculaTheme.FOREGROUND.name()};
                    font-weight: bold;
                    padding: 8px 15px;
                    min-width: 100px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background: {DraculaTheme.PINK.name()};
                }}
            """)
            
            if btn_text == "Reset":
                button.clicked.connect(self.reset_sliders)
            
            setattr(self, f'btn_{btn_text.lower()}', button)
            button_layout.addWidget(button)
        
        # Add the button container to main layout
        main_layout.addWidget(button_container)
        
        # Add stretchable space after buttons
        main_layout.addStretch()

    def reset_sliders(self):
        for axis, control in self.coil_data.controls['axes'].items():
            control.slider.setValue(0)
            control.label.setText("0")
            control.value = 0
        print("All sliders reset to 0")