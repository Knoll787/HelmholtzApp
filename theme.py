from PyQt6.QtGui import QColor, QPalette

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
    # ... rest of palette setup
    
    app.setPalette(palette)
    app.setStyleSheet(f"""
        /* Global stylesheet rules */
    """)