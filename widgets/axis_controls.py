from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, 
                            QGridLayout, QLabel, QComboBox, QSlider)
from PyQt6.QtCore import Qt
from theme import DraculaTheme

class AxisControlsWidget(QWidget):
    def __init__(self, coil_data):
        super().__init__()
        self.coil_data = coil_data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Coil Control")
        title.setAccessibleName("title")
        title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {DraculaTheme.CYAN.name()};
            padding-bottom: 5px;
        """)
        layout.addWidget(title)

        # Axis control group
        axis_group = QGroupBox("Axis Configuration")
        axis_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {DraculaTheme.COMMENT.name()};
                border-radius: 4px;
                margin-top: 10px;
                color: {DraculaTheme.PINK.name()};
            }}
        """)
        
        axis_layout = QGridLayout()
        axis_layout.setHorizontalSpacing(15)
        axis_layout.setVerticalSpacing(10)

        # Column headers
        headers = ["Axis", "Coil Type", "Value"]
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setStyleSheet(f"""
                color: {DraculaTheme.CYAN.name()}; 
                font-weight: bold;
            """)
            axis_layout.addWidget(label, 0, col)

        # Create controls for each axis
        for row, (axis, control) in enumerate(self.coil_data.controls['axes'].items(), start=1):
            # Axis label
            axis_label = QLabel(f"{axis}-Axis")
            axis_label.setStyleSheet(f"color: {DraculaTheme.GREEN.name()};")
            axis_layout.addWidget(axis_label, row, 0)

            # Coil type dropdown
            combo = QComboBox()
            combo.addItems(["Helmholtz", "Maxwell"])
            combo.setCurrentText(control.type)
            combo.setStyleSheet(f"""
                QComboBox {{
                    background: {DraculaTheme.CURRENT_LINE.name()};
                    border: 1px solid {DraculaTheme.COMMENT.name()};
                    min-width: 100px;
                }}
            """)
            combo.currentTextChanged.connect(
                lambda text, a=axis: self.on_coil_type_changed(a, text))
            axis_layout.addWidget(combo, row, 1)
            control.combo = combo

            # Value slider
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(-100, 100)
            slider.setValue(control.value)
            slider.setTickPosition(QSlider.TickPosition.TicksBelow)
            slider.setTickInterval(10)
            slider.setStyleSheet(f"""
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
            """)
            slider.valueChanged.connect(
                lambda value, a=axis: self.on_slider_changed(a, value))
            axis_layout.addWidget(slider, row, 2)
            control.slider = slider

            # Value label
            value_label = QLabel(str(control.value))
            value_label.setStyleSheet(f"""
                color: {DraculaTheme.YELLOW.name()};
                min-width: 30px;
            """)
            axis_layout.addWidget(value_label, row, 3)
            control.label = value_label

        axis_group.setLayout(axis_layout)
        layout.addWidget(axis_group)

    def on_coil_type_changed(self, axis, coil_type):
        self.coil_data.controls['axes'][axis].type = coil_type
        print(f"{axis}-Axis changed to {coil_type} coil")

    def on_slider_changed(self, axis, value):
        control = self.coil_data.controls['axes'][axis]
        control.value = value
        control.label.setText(str(value))
        print(f"{axis}-Axis value: {value}")