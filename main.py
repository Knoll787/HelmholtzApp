import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from theme import apply_dracula_theme
from models.coil_data import CoilData
from widgets.coil_stats import CoilStatsWidget
from widgets.axis_controls import AxisControlsWidget
from widgets.state_buttons import StateButtonsWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.coil_data = CoilData()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Coil Interface")
        self.setFixedSize(800, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        layout.addWidget(CoilStatsWidget(self.coil_data))
        layout.addWidget(AxisControlsWidget(self.coil_data))
        layout.addWidget(StateButtonsWidget(self.coil_data))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_dracula_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())